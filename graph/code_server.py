import asyncio
import getpass
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

if "GROQ_API_KEY" not in os.environ:
    os.environ["GROQ_API_KEY"] = getpass.getpass("Enter your Groq API key: ")


GRAPH_JSON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "graphify-out", "graph.json"
)
server_params = StdioServerParameters(
    command="python", args=["-m", "graphify.serve", GRAPH_JSON]
)

SYSTEM_PROMPT = (
    "You answer questions about a codebase using the Graphify knowledge-graph "
    "tools. Always call a tool before answering — never answer from prior "
    "knowledge. Cite file:line from the tool output."
)


async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Load Graphify's tools (query_graph, get_node, get_neighbors, ...)
            tools = await load_mcp_tools(session)
            print("Loaded tools:", [t.name for t in tools])

            llm = ChatGroq(model="qwen/qwen3.6-27b", max_tokens=4096, temperature=0.6)
            llm_with_tools = llm.bind_tools(tools)

            async def call_model(state: MessagesState):
                messages = state["messages"]
                if not any(isinstance(m, SystemMessage) for m in messages):
                    messages = [SystemMessage(content=SYSTEM_PROMPT), *messages]
                response = await llm_with_tools.ainvoke(messages)
                return {"messages": [response]}

            workflow = StateGraph(MessagesState)
            workflow.add_node("llm", call_model)
            workflow.add_node("tools", ToolNode(tools))

            workflow.add_edge(START, "llm")
            workflow.add_conditional_edges("llm", tools_condition)
            workflow.add_edge("tools", "llm")

            agent = workflow.compile()

            response = await agent.ainvoke(
                {
                    "messages": [
                        HumanMessage(
                            content=(
                                "What is the purpose of the code in "
                                "graph/test.py? Please give a brief summary."
                            )
                        )
                    ]
                },
                # Safety bound instead of a manual call_count — caps tool round-trips.
                config={"recursion_limit": 10},
            )

            last = response["messages"][-1]
            print("content:", repr(last.content))
            print("reasoning:", last.additional_kwargs.get("reasoning_content"))
            print("finish_reason:", last.response_metadata.get("finish_reason"))

            for m in response["messages"]:
                m.pretty_print()

            print("\n=== Final answer ===")
            print(response["messages"][-1].content)


asyncio.run(main())
