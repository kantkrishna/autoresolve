# src/agents/graph.py
import os
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.agents.nodes import (
    triage_node,
    investigation_node,
    resolution_node,
    execution_node,
    review_node
)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    incident_id: str
    tracking_id: str
    proposed_fix: str

def build_incident_graph():
    workflow = StateGraph(AgentState)

    # Define the nodes
    workflow.add_node("triage_node", triage_node)
    workflow.add_node("investigation_node", investigation_node)
    workflow.add_node("resolution_node", resolution_node)
    workflow.add_node("execution_node", execution_node)
    workflow.add_node("review_node", review_node)

    # Define the edges
    workflow.add_edge(START, "triage_node")
    workflow.add_edge("triage_node", "investigation_node")
    workflow.add_edge("investigation_node", "resolution_node")
    workflow.add_edge("resolution_node", "review_node")
    workflow.add_edge("review_node", "execution_node")
    workflow.add_edge("execution_node", END)

    return workflow

# ---------------------------------------------------------
# Phase 10: Persistent Asynchronous PostgreSQL Checkpointing
# ---------------------------------------------------------
DB_URI = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@postgres:5432/autoresolve"
)

# 1. Run schema migrations synchronously to create tables safely if missing
with psycopg.connect(DB_URI, autocommit=True) as schema_conn:
    from langgraph.checkpoint.postgres import PostgresSaver
    PostgresSaver(schema_conn).setup()

# 2. The Just-In-Time (JIT) Async Graph Runner
# This defers asyncio-dependent instantiations until the event loop is actually running
class AsyncGraphRunner:
    def __init__(self):
        self._app = None
        self._pool = None

    async def _init_app(self):
        # Only initialize once, and only when called from within an active async loop
        if self._app is None:
            self._pool = AsyncConnectionPool(
                conninfo=DB_URI,
                max_size=10,
                kwargs={"autocommit": True, "row_factory": dict_row}
            )
            await self._pool.open()
            
            # Now that we are inside the active loop, this will succeed!
            checkpointer = AsyncPostgresSaver(self._pool)
            
            workflow = build_incident_graph()
            self._app = workflow.compile(
                checkpointer=checkpointer,
                interrupt_before=["execution_node"]
            )

    # Forward LangGraph asynchronous methods transparently
    async def astream(self, *args, **kwargs):
        await self._init_app()
        async for chunk in self._app.astream(*args, **kwargs):
            yield chunk

    async def aget_state(self, *args, **kwargs):
        await self._init_app()
        return await self._app.aget_state(*args, **kwargs)

    async def aupdate_state(self, *args, **kwargs):
        await self._init_app()
        return await self._app.aupdate_state(*args, **kwargs)

# Export the JIT wrapper seamlessly as 'app'
# This requires zero changes to worker.py or approve.py!
app = AsyncGraphRunner()