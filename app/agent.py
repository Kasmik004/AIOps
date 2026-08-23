import asyncio
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain_mcp_adapters import client
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

load_dotenv()  # Load environment variables from .env file

DATABASE_URL = os.getenv("DATABASE_URL")


async def run_agent(command=None, chat_id=None):
    client = MultiServerMCPClient(
        {
            "GitHubHelper": {
                "command": "uv",
                "args": ["run", "python", "../mcp_server/server.py"],
                "transport": "stdio",
            }
        }
    )
    tools = await client.get_tools()

    llm = ChatGroq(model="qwen/qwen3.6-27b", temperature=0)

    llm_with_tools = llm.bind_tools(tools)

    async def call_model(state: MessagesState):
        messages = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [
                SystemMessage(content="You are a helpful GitHub Helper Agent.")
            ] + messages
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    tool_node = ToolNode(tools)

    workflow = StateGraph(MessagesState)

    workflow.add_node("tools", tool_node)
    workflow.add_node("llm", call_model)

    workflow.add_edge(START, "llm")
    workflow.add_conditional_edges("llm", tools_condition)
    workflow.add_edge("tools", "llm")

    # app = workflow.compile()

    async with AsyncPostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
        await checkpointer.setup()
        app = workflow.compile(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": chat_id}}

        inputs = (
            {"messages": [HumanMessage(content=command)]}
            if command
            else {
                "messages": [
                    HumanMessage(
                        content="Create a GitHub issue with title 'Test Issue' and body 'This is a test issue.'"
                    )
                ]
            }
        )

        final_response = "I have processed your request, but I cannot provide a response at this time."

        async for chunk in app.astream(inputs, config=config, stream_mode="values"):
            last_msg = chunk["messages"][-1]

            if last_msg.type == "ai" and last_msg.content:
                final_response = last_msg.content

        return final_response
    # response = await app.ainvoke(inputs)
    # messages = response["messages"]
    # return (
    #     messages[-1].content if messages else "Failed to get a response from the agent."
    # )


if __name__ == "__main__":
    response = asyncio.run(run_agent())
    print(response)
