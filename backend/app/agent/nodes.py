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

# Async client for Ollama
client = ollama.AsyncClient(host=settings.OLLAMA_BASE_URL)

async def reason_node(state: AgentState):
    """
    Decides if tool call needed, selects tool using DeepSeek-R1 reasoning.
    """
    messages = state["messages"]
    
    # Prepare prompt with tool definitions
    tool_schemas = server.get_tool_schemas()
    
    # Enhancing prompt for DeepSeek-R1 tool selection
    prompt = f"{SYSTEM_PROMPT}\n\n"
    prompt += "### Available Tools\n"
    prompt += f"{json.dumps(tool_schemas, indent=2)}\n\n"
    prompt += "### Instructions\n"
    prompt += "1. Analyze the user's query and decide if you need to call a tool.\n"
    prompt += "2. If you need a tool, respond with ONLY a JSON object in this format:\n"
    prompt += '   {"tool_calls": [{"name": "tool_name", "args": {"arg1": "val1"}}]}\n'
    prompt += "3. If no tool is needed, provide your reasoning and final answer directly.\n"
    prompt += "4. If you have already received tool results in the conversation, synthesize the final answer.\n"

    # Convert LangChain messages to Ollama format
    ollama_messages = [{"role": "system", "content": prompt}]
    for msg in messages:
        if isinstance(msg, HumanMessage):
            ollama_messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            ollama_messages.append({"role": "assistant", "content": msg.content})
        elif isinstance(msg, ToolMessage):
            ollama_messages.append({"role": "system", "content": f"Tool Result: {msg.content}"})

    response = await client.chat(
        model=settings.LLM_MODEL_NAME,
        messages=ollama_messages,
    )
    
    content = response['message']['content']
    
    # Check for tool calls in the response content
    tool_calls = []
    try:
        # Match JSON pattern for tool_calls
        match = re.search(r'\{.*"tool_calls".*\}', content, re.DOTALL)
        if match:
            json_str = match.group(0)
            data = json.loads(json_str)
            tool_calls = data.get("tool_calls", [])
            # If it's a tool call, we might want to strip the JSON from content 
            # or keep it. For LangGraph, we need to return the tool_calls.
            # We'll normalize tool_calls to include an ID if missing
            for i, tc in enumerate(tool_calls):
                if "id" not in tc:
                    tc["id"] = f"call_{i}"
    except Exception as e:
        print(f"Error parsing tool calls: {e}")

    # Create AIMessage. In LangGraph, we add it to the state.
    ai_msg = AIMessage(content=content)
    if tool_calls:
        # LangChain's AIMessage expects tool_calls in a specific format
        ai_msg.tool_calls = tool_calls

    return {
        "messages": [ai_msg],
        "tool_calls": tool_calls
    }

async def tool_call_node(state: AgentState):
    """
    Executes MCP tool call and returns results as ToolMessages.
    """
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
        new_messages.append(ToolMessage(
            content=json.dumps(result),
            tool_call_id=call_id
        ))
        
    return {
        "messages": new_messages,
        "tool_results": tool_results
    }

async def rag_retrieve_node(state: AgentState):
    """
    Retrieves relevant strategy context from Qdrant.
    """
    # Find the last human message
    last_user_message = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_message = msg.content
            break
            
    if not last_user_message:
        return {"retrieved_context": []}
        
    print(f"Retrieving RAG context for: {last_user_message[:50]}...")
    try:
        query_emb = embed_texts([last_user_message])[0]
        results = search_strategies(query_emb, top_k=3)
        context = [res["text"] for res in results]
        return {"retrieved_context": context}
    except Exception as e:
        print(f"RAG Retrieval Error: {e}")
        return {"retrieved_context": []}

async def synthesize_node(state: AgentState):
    """
    Combines tool results + RAG context + model reasoning into a final answer.
    """
    messages = state["messages"]
    retrieved_context = state.get("retrieved_context", [])
    tool_results = state.get("tool_results", [])
    
    # Prepare synthesis instructions
    synth_prompt = "### Final Synthesis Instructions\n"
    synth_prompt += "1. Combine the retrieved knowledge base context and the real-time tool results.\n"
    synth_prompt += "2. Provide a professional, quantitative, and actionable response.\n"
    synth_prompt += "3. Ensure all mathematical derivations are shown if applicable.\n"
    synth_prompt += "4. Include the required risk disclaimer.\n\n"
    
    if retrieved_context:
        synth_prompt += "### Knowledge Base Context\n"
        synth_prompt += json.dumps(retrieved_context, indent=2) + "\n\n"
        
    if tool_results:
        synth_prompt += "### Real-time Tool Results\n"
        synth_prompt += json.dumps(tool_results, indent=2) + "\n\n"

    ollama_messages = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\n{synth_prompt}"}
    ]
    
    for msg in messages:
        if isinstance(msg, HumanMessage):
            ollama_messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            # Skip messages that were just tool call JSONs
            if '"tool_calls"' not in msg.content:
                ollama_messages.append({"role": "assistant", "content": msg.content})
        elif isinstance(msg, ToolMessage):
            # Already included via synth_prompt usually, but we can add if needed
            pass

    response = await client.chat(
        model=settings.LLM_MODEL_NAME,
        messages=ollama_messages,
    )
    
    final_content = response['message']['content']
    
    return {
        "messages": [AIMessage(content=final_content)]
    }
