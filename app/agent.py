import asyncio
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain_mcp_adapters import client
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    trim_messages,
    ToolMessage,
)
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import interrupt, Command

from typing import Annotated
from functools import reduce


from logging import getLogger

logger = logging.getLogger("aiops")

load_dotenv()  # Load environment variables from .env file

DATABASE_URL = os.getenv("DATABASE_URL")


# def merge_tools(current: set[str], new: set[str]) -> set[str]:
#     return current | new


class AgentState(MessagesState):
    accepted_tools: set[str]


def normalize_message_text(message) -> str:
    if message is None:
        return ""

    content = getattr(message, "content", message)

    if isinstance(content, str):
        clean = content.strip()
        if clean:
            return clean

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item and item["text"]:
                parts.append(str(item["text"]).strip())
            elif hasattr(item, "text") and item.text:
                parts.append(str(item.text).strip())
        joined = " ".join(p for p in parts if p)
        if joined:
            return joined

    tool_calls = getattr(message, "tool_calls", None)
    if tool_calls:
        first_tool = tool_calls[0]
        name = (
            first_tool.get("name")
            if isinstance(first_tool, dict)
            else getattr(first_tool, "name", "tool")
        )
        return f"I need your approval before I run the {name} tool."

    return ""


def get_mcp_server_config():
    project_root = Path(__file__).resolve().parent.parent
    server_script = project_root / "mcp_server" / "server.py"
    return {
        "command": sys.executable,
        "args": [str(server_script)],
        "transport": "stdio",
        "cwd": str(project_root),
    }


def get_graphify_server_config():
    project_root = Path(__file__).resolve().parent.parent
    GRAPH_JSON = project_root.parent / "first_steps" / "graphify-out" / "graph.json"

    server_params = {
        "command": "python",
        "args": ["-m", "graphify.serve", str(GRAPH_JSON)],
        "transport": "stdio",
    }
    return server_params


async def run_agent(command=None, chat_id=None, resume_decision=None):
    client = MultiServerMCPClient(
        {
            "GitHubHelper": get_mcp_server_config(),
            "graphify": get_graphify_server_config(),
        }
    )
    tools = await client.get_tools()

    # print("hi")

    # tool_list = [tool.name for tool in tools]

    # return tool_list  # Return the tools for inspection

    logger.info(f"Available tools: {[tool.name for tool in tools]}")

    llm = ChatGroq(model="qwen/qwen3.6-27b", temperature=0)

    llm_with_tools = llm.bind_tools(tools)

    async def call_model(state: AgentState) -> AgentState:
        messages = state["messages"]
        logger.info(f"Calling model with messages: {[m.content for m in messages]}")

        trimmed_messages = trim_messages(
            state["messages"], max_tokens=15, strategy="last", token_counter=len
        )
        if not any(isinstance(m, SystemMessage) for m in trimmed_messages):
            trimmed_messages = [
                SystemMessage(content="You are a helpful GitHub Helper Agent.")
            ] + trimmed_messages
        response = await llm_with_tools.ainvoke(trimmed_messages)
        logger.info(f"Model response: {response}")
        return {
            "messages": [response],
            "accepted_tools": state.get("accepted_tools", set()),
        }
        # raise RuntimeError("Server crashed mid-execution.")

    def human_approval(state: AgentState):
        last_message = state["messages"][-1]
        logger.info("Human Approval Section: Last message from model:")
        logger.info(f"Last message from model: {last_message}")

        tool_call = last_message.tool_calls[0]

        if tool_call["name"] in state["accepted_tools"]:
            logger.info(
                f"Tool {tool_call['name']} already approved. Proceeding to tools."
            )
            return Command(goto="tools")

        decision = interrupt(
            {"description": f"The agent wants to execute: `{tool_call['name']}`"}
        )

        logger.info(f"Human approval decision: {decision}")
        if decision == "approve":
            logger.info("Human approved the action. Proceeding to tools.")
            accepted_tools = state.get("accepted_tools", set())
            accepted_tools = accepted_tools | {tool_call["name"]}
            return Command(update={"accepted_tools": accepted_tools}, goto="tools")

        logger.info("Human rejected the action. Returning to LLM.")
        reject_msgs = [
            ToolMessage(tool_call_id=tc["id"], content="Action rejected by the human.")
            for tc in last_message.tool_calls
        ]

        return Command(update={"messages": reject_msgs}, goto="llm")

    tool_node = ToolNode(tools)

    workflow = StateGraph(AgentState)

    workflow.add_node("tools", tool_node)
    workflow.add_node("llm", call_model)
    workflow.add_node("human_approval", human_approval)

    workflow.add_edge(START, "llm")
    workflow.add_conditional_edges(
        "llm", tools_condition, {"tools": "human_approval", END: END}
    )
    workflow.add_edge("tools", "llm")

    # app = workflow.compile()

    if not DATABASE_URL:
        raise ValueError(
            "DATABASE_URL environment variable is missing. Please set it to your PostgreSQL connection string."
        )
    async with AsyncPostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
        await checkpointer.setup()
        app = workflow.compile(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": chat_id}}

        if resume_decision:
            inputs = Command(resume=resume_decision)

        else:
            inputs = (
                {"messages": [HumanMessage(content=command)]}
                if command
                else {"messages": [HumanMessage(content="Hi.")]}
            )

        final_response = "I have processed your request, but I cannot provide a response at this time."

        result = {"text": final_response, "interrupt": None}

        async for chunk in app.astream(inputs, config=config, stream_mode="updates"):
            if "__interrupt__" in chunk:
                result["interrupt"] = chunk["__interrupt__"][0].value
                result["text"] = (
                    f"I need your approval before I run: "
                    f"{result['interrupt'].get('description', 'this GitHub action')}."
                )
                break

            if "llm" in chunk:
                messages = chunk["llm"].get("messages", [])
                if messages:
                    last_msg = messages[-1]
                    if isinstance(last_msg, AIMessage):
                        normalized = normalize_message_text(last_msg)
                        if normalized:
                            result["text"] = normalized
                        elif getattr(last_msg, "tool_calls", None):
                            result["text"] = (
                                "I need your approval before I run this GitHub action."
                            )

        return result
    # response = await app.ainvoke(inputs)
    # messages = response["messages"]
    # return (
    #     messages[-1].content if messages else "Failed to get a response from the agent."
    # )


if __name__ == "__main__":
    response = asyncio.run(run_agent())
    print(response)
    # print(response)
