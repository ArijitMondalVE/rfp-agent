from typing import TypedDict

from langgraph.graph import StateGraph, END

from app.agents.scope_agent import extract_scope
from app.agents.timeline_agent import extract_deadlines


class RFPState(TypedDict):

    text: str

    scope: str

    deadlines: str


def scope_node(state):

    scope = extract_scope(state["text"])

    return {
        "scope": scope
    }


def deadline_node(state):

    deadlines = extract_deadlines(state["text"])

    return {
        "deadlines": deadlines
    }


workflow = StateGraph(RFPState)

workflow.add_node("scope_agent", scope_node)

workflow.add_node("timeline_agent", deadline_node)

workflow.set_entry_point("scope_agent")

workflow.add_edge("scope_agent", "timeline_agent")

workflow.add_edge("timeline_agent", END)

graph = workflow.compile()