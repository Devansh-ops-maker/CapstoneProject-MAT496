from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, List, Dict, Any
import requests
from urllib.parse import quote
import base64
import json

class AssistantState(TypedDict):
    user_id: str
    session_id: str
    query: str
    memories: Dict[str, str]
    history: List[Dict[str, str]]
    route: str
    responses: List[Dict[str, Any]]
    selected: Dict[str, Any]
    refined: str
    result: Dict[str, Any]


def extract_memory(state: AssistantState):
    return state

def load_context(state: AssistantState):
    state["memories"] = {}
    state["history"] = []
    return state

def route_query(state: AssistantState):
    state["route"] = "direct_llm"
    return state

def run_tool(state: AssistantState):
    state["responses"] = state.get("responses", [])
    state["responses"].append({
        "content": "Tool result",
        "source": "tool",
        "confidence": 0.9
    })
    return state

def run_rag(state: AssistantState):
    state["responses"] = state.get("responses", [])
    state["responses"].append({
        "content": "RAG result",
        "source": "rag",
        "confidence": 0.7
    })
    return state

def run_llm(state: AssistantState):
    state["responses"] = state.get("responses", [])
    state["responses"].append({
        "content": "LLM result",
        "source": "direct_llm",
        "confidence": 0.6
    })
    return state

def collect(state: AssistantState):
    return state

def select_best(state: AssistantState):
    if state.get("responses"):
        state["selected"] = state["responses"][0]
    else:
        state["selected"] = {}
    return state

def refine(state: AssistantState):
    state["refined"] = state.get("selected", {}).get("content", "")
    return state

def store(state: AssistantState):
    state["result"] = state.get("selected", {})
    return state

def end_node(state: AssistantState):
    return state


def build_graph():
    g = StateGraph(AssistantState)

    g.add_node("extract_memory", extract_memory)
    g.add_node("load_context", load_context)
    g.add_node("route_query", route_query)
    g.add_node("run_tool", run_tool)
    g.add_node("run_rag", run_rag)
    g.add_node("run_llm", run_llm)
    g.add_node("collect", collect)
    g.add_node("select", select_best)
    g.add_node("refine", refine)
    g.add_node("store", store)
    g.add_node("end", end_node)

    g.set_entry_point("extract_memory")

    g.add_edge("extract_memory", "load_context")
    g.add_edge("load_context", "route_query")

    g.add_conditional_edges(
        "route_query",
        lambda s: s["route"],
        {
            "tool": "run_tool",
            "rag": "run_rag",
            "direct_llm": "run_llm"
        }
    )

    g.add_edge("run_tool", "collect")
    g.add_edge("run_rag", "collect")
    g.add_edge("run_llm", "collect")

    g.add_edge("collect", "select")
    g.add_edge("select", "refine")
    g.add_edge("refine", "store")
    g.add_edge("store", "end")

    return g.compile()


def generate_mermaid_code():
    mermaid_code = """graph TD
    A[extract_memory] --> B[load_context]
    B --> C{route_query}
    
    C -->|tool| D[run_tool]
    C -->|rag| E[run_rag]
    C -->|direct_llm| F[run_llm]
    
    D --> G[collect]
    E --> G
    F --> G
    
    G --> H[select]
    H --> I[refine]
    I --> J[store]
    J --> K[end]
    
    style A fill:#e1f5fe
    style B fill:#e1f5fe
    style C fill:#fff3e0
    style D fill:#f3e5f5
    style E fill:#e8f5e8
    style F fill:#fff3e0
    style G fill:#f1f8e9
    style H fill:#fff3e0
    style I fill:#e0f7fa
    style J fill:#f1f8e9
    style K fill:#e8f5e8
    
    classDef init fill:#e1f5fe
    classDef decision fill:#fff3e0
    classDef tool fill:#f3e5f5
    classDef rag fill:#e8f5e8
    classDef llm fill:#fff3e0
    classDef memory fill:#e0f7fa
    classDef final fill:#e8f5e8
    
    class A,B init
    class C decision
    class D tool
    class E rag
    class F llm
    class I memory
    class J,K final"""
    
    return mermaid_code


def generate_png_diagram():
    mermaid_code = generate_mermaid_code()
    encoded_mermaid = base64.b64encode(mermaid_code.encode()).decode()
    url = f"https://mermaid.ink/img/{encoded_mermaid}?bgColor=ffffff&theme=default"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open("assistant_langgraph.png", 'wb') as f:
                f.write(response.content)
            return True
        else:
            with open("assistant_langgraph.mermaid", "w") as f:
                f.write(mermaid_code)
            return False
    except requests.exceptions.RequestException:
        with open("assistant_langgraph.mermaid", "w") as f:
            f.write(mermaid_code)
        return False


if __name__ == "__main__":
    graph = build_graph()
    success = generate_png_diagram()
