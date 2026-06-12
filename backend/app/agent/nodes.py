import json
import ollama
import re
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from .state import AgentState
from ..mcp.server import server
from ..rag.qdrant_client import search_strategies
from ..rag.embedder import embed_texts
from .prompts import SYSTEM_PROMPT
from ..config import settings
from ..nl_parser import nl_parser

client = ollama.AsyncClient(host=settings.OLLAMA_BASE_URL)

async def reason_node(state: AgentState):
    messages = state["messages"]
    last_user_msg = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break

    parsed = nl_parser.parse(last_user_msg)
    if parsed:
        response_content = json.dumps(parsed)
        ai_msg = AIMessage(content=response_content)
        tool_calls = [{
            "id": "call_nl_parsed",
            "name": "run_backtest",
            "args": parsed.get("params", {})
        }]
        ai_msg.tool_calls = tool_calls
        return {"messages": [ai_msg], "tool_calls": tool_calls, "retrieved_context": []}

    tool_schemas = server.get_tool_schemas()
    prompt = f"{SYSTEM_PROMPT}\n\n"
    prompt += "### Available Tools\n"
    prompt += f"{json.dumps(tool_schemas, indent=2)}\n\n"
    prompt += "### Instructions\n"
    prompt += "1. Analyze the user's query.\n"
    prompt += "2. If backtesting, respond with the JSON format shown above including 'action': 'run_backtest'.\n"
    prompt += "3. For market data/questions, respond conversationally.\n"
    prompt += "4. If you need a tool, respond with ONLY a JSON: {\"tool_calls\": [{\"name\": \"tool_name\", \"args\": {...}}]}\n"

    ollama_messages = [{"role": "system", "content": prompt}]
    for msg in messages:
        if isinstance(msg, HumanMessage):
            ollama_messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            ollama_messages.append({"role": "assistant", "content": msg.content})
        elif isinstance(msg, ToolMessage):
            ollama_messages.append({"role": "system", "content": f"Tool Result: {msg.content}"})

    response = await client.chat(model=settings.LLM_MODEL_NAME, messages=ollama_messages)
    content = response['message']['content']

    tool_calls = []
    try:
        match = re.search(r'\{.*"tool_calls".*\}', content, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            tool_calls = data.get("tool_calls", [])
            for i, tc in enumerate(tool_calls):
                if "id" not in tc:
                    tc["id"] = f"call_{i}"

        bt_match = re.search(r'\{.*"action":\s*"run_backtest".*\}', content, re.DOTALL)
        if bt_match:
            data = json.loads(bt_match.group(0))
            params = data.get("params", {})
            tool_calls.append({
                "id": "call_bt",
                "name": "run_backtest",
                "args": params
            })
    except Exception as e:
        print(f"Error parsing: {e}")

    ai_msg = AIMessage(content=content)
    if tool_calls:
        ai_msg.tool_calls = tool_calls

    return {"messages": [ai_msg], "tool_calls": tool_calls}

async def tool_call_node(state: AgentState):
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", [])

    if not tool_calls:
        return {}

    new_messages = []
    tool_results = []

    for tool_call in tool_calls:
        name = tool_call["name"]
        args = tool_call["args"]
        call_id = tool_call.get("id", "default")
        print(f"Executing Tool: {name} with args: {args}")
        result = await server.execute_tool(name, args)
        tool_results.append({"tool": name, "result": result})
        new_messages.append(ToolMessage(content=json.dumps(result), tool_call_id=call_id))

    return {"messages": new_messages, "tool_results": tool_results}

async def rag_retrieve_node(state: AgentState):
    last_user_message = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break

    if not last_user_message:
        return {"retrieved_context": []}

    try:
        query_emb = embed_texts([last_user_message])[0]
        results = search_strategies(query_emb, top_k=3)
        context = [res["text"] for res in results]
        return {"retrieved_context": context}
    except Exception as e:
        print(f"RAG Retrieval Error: {e}")
        return {"retrieved_context": []}

async def synthesize_node(state: AgentState):
    messages = state["messages"]
    retrieved_context = state.get("retrieved_context", [])
    tool_results = state.get("tool_results", [])

    has_backtest = False
    for tr in tool_results:
        if tr.get("tool") == "run_backtest" and "error" not in str(tr.get("result", {})):
            has_backtest = True
            break

    if has_backtest and tool_results:
        bt_result = None
        for tr in tool_results:
            if tr.get("tool") == "run_backtest":
                bt_result = tr.get("result", {})
                break
        if bt_result:
            response_parts = [f"## Backtest Results\n"]
            response_parts.append(f"- **Total Return**: {bt_result.get('total_return', 0):.2f}%")
            response_parts.append(f"- **Sharpe Ratio**: {bt_result.get('sharpe', 0):.2f}")
            response_parts.append(f"- **Max Drawdown**: {bt_result.get('max_drawdown', 0):.2f}%")
            response_parts.append(f"- **Win Rate**: {bt_result.get('win_rate', 0):.1f}%")
            response_parts.append(f"- **Total Trades**: {bt_result.get('total_trades', 0)}")
            if bt_result.get('cagr'):
                response_parts.append(f"- **CAGR**: {bt_result.get('cagr', 0):.2f}%")
            if bt_result.get('calmar'):
                response_parts.append(f"- **Calmar Ratio**: {bt_result.get('calmar', 0):.2f}")
            response_parts.append("\n⚠️ Past performance does not guarantee future results.")
            return {"messages": [AIMessage(content="\n".join(response_parts))]}

    synth_prompt = "### Final Synthesis Instructions\n"
    synth_prompt += "1. Combine the retrieved knowledge base context and the real-time tool results.\n"
    synth_prompt += "2. Provide a professional, quantitative, and actionable response.\n"
    synth_prompt += "3. Include the required risk disclaimer.\n\n"

    if retrieved_context:
        synth_prompt += "### Knowledge Base Context\n" + json.dumps(retrieved_context, indent=2) + "\n\n"
    if tool_results:
        synth_prompt += "### Real-time Tool Results\n" + json.dumps(tool_results, indent=2) + "\n\n"

    ollama_messages = [{"role": "system", "content": f"{SYSTEM_PROMPT}\n\n{synth_prompt}"}]
    for msg in messages:
        if isinstance(msg, HumanMessage):
            ollama_messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            if '"tool_calls"' not in msg.content:
                ollama_messages.append({"role": "assistant", "content": msg.content})

    response = await client.chat(model=settings.LLM_MODEL_NAME, messages=ollama_messages)
    final_content = response['message']['content']
    return {"messages": [AIMessage(content=final_content)]}
