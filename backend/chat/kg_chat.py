"""
Provides a conversational interface over the Neo4j knowledge graph
built by exporters/kg_builder.py.

Uses LangChain's Neo4jGraph + GraphCypherQAChain under the hood, but
wraps it in a smarter router so the LLM isn't handed raw schema every time.

Features
────────
  • Auto-discovers the graph schema from Neo4j on startup
  • Routes to Cypher generation ONLY when the question needs graph traversal
  • Falls back to direct LLM answer for general questions
  • Maintains conversational memory across turns
  • Pretty-prints Cypher that was generated (debug mode)

Usage
─────
    from chat.kg_chat import KGChat

    chat = KGChat(
        neo4j_uri      = "bolt://localhost:7687",
        neo4j_user     = "neo4j",
        neo4j_password = "yourpassword",
        model          = "gemini-2.5-flash",
        debug          = False,
    )
"""

from __future__ import annotations

import os
from typing import Optional

from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser


# ─────────────────────────────────────────────────────────────────────────────
# Prompt templates
# ─────────────────────────────────────────────────────────────────────────────

_CYPHER_GENERATION_TEMPLATE = """
You are an expert Neo4j Cypher query writer for a database schema knowledge graph.

The graph has these node labels and properties:
  (:Database)  {{ name, updated_at }}
  (:Table)     {{ fqn, name, database, pk }}
  (:Column)    {{ fqn, name, type, table_fqn, is_pk }}

Relationship types:
  (:Database)-[:HAS_TABLE]->(:Table)
  (:Table)-[:HAS_COLUMN]->(:Column)
  (:Table)-[:RELATES_TO {{via_column, referred_column}}]->(:Table)
  (:Column)-[:IS_PK_OF]->(:Table)
  (:Column)-[:IS_FK_TO {{referred_column}}]->(:Table)

Rules:
- fqn looks like "bike_store.db.tablename" for Tables
  and "bike_store.db.tablename.colname" for Columns.
- Always query by t.name or c.name, NOT by fqn.
- Always use MATCH, never CREATE or DELETE.
- Return human-readable properties, not raw node objects.
- If listing columns, return c.name and c.type at minimum.
- Limit results to 50 unless asked for more.

Path-finding rules (CRITICAL):
- RELATES_TO edges point FROM the table with the FK TO the referenced table.
  e.g. order_items-[:RELATES_TO]->orders  (order_items.order_id references orders)
- For ANY path or traversal question between two tables, ALWAYS use undirected
  relationships with NO arrow:
    (t1)-[:RELATES_TO*1..5]-(t2)   ← correct, finds paths in either direction
    (t1)-[:RELATES_TO*1..5]->(t2)  ← WRONG, will miss reverse paths
- Never use directed -> for path traversal questions.
- For "which tables to join" questions, find the path and return all table names.

Schema context:
{schema}

Question: {question}

Cypher query (no markdown, just the query):
"""

_CYPHER_QA_TEMPLATE = """
You are a helpful data dictionary assistant. Answer the user's question based on the
Cypher query results. Be concise, use plain English, and format lists nicely.

If results are empty, say the information was not found in the schema.

Question: {question}
Cypher results: {context}

Answer:
"""

_ROUTER_TEMPLATE = """
Classify the user question into one of two categories:
  GRAPH  – needs querying Neo4j (schema structure, columns, relationships,
            table info, FK chains, lineage, join paths, etc.)
  DIRECT – can be answered from general knowledge without graph lookup
            (explanations of SQL concepts, generic advice, small talk, etc.)

Respond with exactly one word: GRAPH or DIRECT.

Question: {question}
"""


# ─────────────────────────────────────────────────────────────────────────────
# KGChat
# ─────────────────────────────────────────────────────────────────────────────


class KGChat:
    """
    Conversational interface over the Neo4j schema knowledge graph.
    """

    def __init__(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        google_api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
        debug: bool = False,
    ):
        self.debug = debug

        # ── Neo4j graph ───────────────────────────────────────────────────────
        self.graph = Neo4jGraph(
            url=neo4j_uri,
            username=neo4j_user,
            password=neo4j_password,
        )
        self.graph.refresh_schema()

        # ── LLM ───────────────────────────────────────────────────────────────
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Set GEMINI_API_KEY in your .env file.")

        self.llm = ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", model),
            temperature=0,
            google_api_key=api_key,
        )

        # ── Memory ────────────────────────────────────────────────────────────
        self.memory = InMemoryChatMessageHistory()

        # ── Cypher QA chain ───────────────────────────────────────────────────
        cypher_prompt = PromptTemplate(
            input_variables=["schema", "question"],
            template=_CYPHER_GENERATION_TEMPLATE,
        )
        qa_prompt = PromptTemplate(
            input_variables=["question", "context"],
            template=_CYPHER_QA_TEMPLATE,
        )

        self.cypher_chain = GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph=self.graph,
            cypher_prompt=cypher_prompt,
            qa_prompt=qa_prompt,
            verbose=debug,
            return_intermediate_steps=debug,
            allow_dangerous_requests=True,
        )

        # ── Router chain ──────────────────────────────────────────────────────
        router_prompt = PromptTemplate(
            input_variables=["question"],
            template=_ROUTER_TEMPLATE,
        )
        self.router_chain = router_prompt | self.llm | StrOutputParser()

        print("[KGChat] Ready. Graph schema loaded from Neo4j.")

    # ── Public API ────────────────────────────────────────────────────────────

    def ask(self, question: str) -> str:
        route = self._route(question)

        if self.debug:
            print(f"[Router] → {route}")

        answer = self._graph_answer(question) if route == "GRAPH" else self._direct_answer(question)

        self.memory.add_user_message(question)
        self.memory.add_ai_message(answer)

        return answer

    def reset_memory(self):
        self.memory.clear()
        print("[KGChat] Memory cleared.")

    # ── Private ───────────────────────────────────────────────────────────────

    def _route(self, question: str) -> str:
        result = self.router_chain.invoke({"question": question}).strip().upper()
        return "GRAPH" if "GRAPH" in result else "DIRECT"

    def _graph_answer(self, question: str) -> str:
        history = self._history_text()
        augmented = f"{history}\nUser: {question}" if history else question

        try:
            result = self.cypher_chain.invoke({"query": augmented})
            if self.debug and "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    print(f"  [Cypher] {step}")
            return result.get("result", "No results found in the graph.")
        except Exception as e:
            return f"Graph query failed: {e}. Try rephrasing your question."

    def _direct_answer(self, question: str) -> str:
        history = self._history_text()
        system = "You are a helpful data dictionary assistant. Answer clearly and concisely."
        messages = [SystemMessage(content=system)]
        if history:
            messages.append(HumanMessage(content=f"Conversation so far:\n{history}"))
        messages.append(HumanMessage(content=question))
        return self.llm.invoke(messages).content

    def _history_text(self) -> str:
        msgs = self.memory.messages[-20:]
        if not msgs:
            return ""
        lines = []
        for m in msgs:
            role = "User" if isinstance(m, HumanMessage) else "Assistant"
            lines.append(f"{role}: {m.content}")
        return "\n".join(lines)