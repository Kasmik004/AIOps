import asyncio
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()  # Load environment variables from .env file


async def run_agent():
    async with MultiServerMCPClient(
        {
            "GitHubHelper": {
                "command": "uv run python",
                "args": ["mcp_server/server.py"],
            }
        }
    ) as mcp_client:

        tools = await mcp_client.get_tools()

        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

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

        app = workflow.compile()

        user_input = f"Create an issue in my repo '{os.getenv('GITHUB_REPO')}' titled 'Test Issue' with body 'This is a test issue.'."
        inputs = {"messages": [HumanMessage(content=user_input)]}

        print("Starting graph execution...\n")
        async for chunk in app.astream(inputs, stream_mode="values"):
            # Print the last message added to the state at each step
            chunk["messages"][-1].pretty_print()


if __name__ == "__main__":
    asyncio.run(run_agent())
