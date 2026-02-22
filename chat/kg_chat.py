"""
Provides a conversational interface over the Neo4j knowledge graph
built by exporters/kg_builder.py.

Uses LangChain's Neo4jGraph + GraphCypherQAChain under the hood, but
wraps it in a smarter router so the LLM isn't handed raw schema every time.

Features
────────
  • Auto-discovers the graph schema from Neo4j on startup
  • Builds a rich system prompt from node/edge structure
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
        google_api_key = "sk-...", # or set OPENAI_API_KEY env var
        model: str = "gemini-3-flash-preview", # any chat model
        debug          = False,
    )

    while True:
        q = input("You: ").strip()
        if q.lower() in ("exit", "quit"):
            break
        answer = chat.ask(q)
        print(f"Assistant: {answer}")
"""

from __future__ import annotations

import os
from typing import Optional

# ── LangChain imports ─────────────────────────────────────────────────────────

from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser


# ─────────────────────────────────────────────────────────────────────────────
# Prompt templates
# ─────────────────────────────────────────────────────────────────────────────

# Tells the LLM how to write Cypher for OUR specific graph schema
_CYPHER_GENERATION_TEMPLATE = """
You are an expert Neo4j Cypher query writer for a database schema knowledge graph.

The graph has these node labels and properties:
  (:Database)  {{ name, updated_at }}
  (:Table)     {{ fqn, name, database, pk, row_count }}
  (:Column)    {{ fqn, name, type, table_fqn, is_pk,
                  completeness, non_null,
                  stat_min, stat_max, stat_avg, stat_stddev,
                  latest_value, age_days }}

Relationship types:
  (:Database)-[:HAS_TABLE]->(:Table)
  (:Table)-[:HAS_COLUMN]->(:Column)
  (:Table)-[:RELATES_TO {{via_column, referred_column}}]->(:Table)
  (:Column)-[:IS_PK_OF]->(:Table)
  (:Column)-[:IS_FK_TO {{referred_column}}]->(:Table)

Rules:
- fqn (fully qualified name) looks like "mydb.tablename" for Tables
  and "mydb.tablename.colname" for Columns.
- Always use MATCH, never CREATE or DELETE.
- Return human-readable property names, not raw node objects.
- If listing columns, return c.name and c.type at minimum.
- For relationship traversal questions, follow RELATES_TO edges.
- Limit results to 50 unless asked for more.

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
            data quality, table info, FK chains, lineage, etc.)
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
        model: str = "gemini-3-flash-preview",
        debug: bool = False,
    ):
        self.debug = debug

        # ── Neo4j graph (LangChain wrapper) ───────────────────────────────────
        self.graph = Neo4jGraph(
            url=neo4j_uri,
            username=neo4j_user,
            password=neo4j_password,
        )
        # Refresh schema from the live graph
        self.graph.refresh_schema()

        # ── LLM ───────────────────────────────────────────────────────────────
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Pass gemini_api_key or set GEMINI_API_KEY env var.")

        self.llm = ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL"),
            temperature=0,
            google_api_key=api_key,
        )

        # ── Memory (last 10 turns) ─────────────────────────────────────────────
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
            allow_dangerous_requests=True,  # we only run MATCH queries
        )

        # ── Router chain (tiny, fast) ─────────────────────────────────────────
        router_prompt = PromptTemplate(
            input_variables=["question"],
            template=_ROUTER_TEMPLATE,
        )
        self.router_chain = router_prompt | self.llm | StrOutputParser()

        print("[KGChat] Ready. Graph schema loaded from Neo4j.")

    # ── Public API ────────────────────────────────────────────────────────────

    def ask(self, question: str) -> str:
        """
        Route the question, hit Neo4j or LLM directly, update memory.
        """
        route = self._route(question)

        if self.debug:
            print(f"[Router] → {route}")

        if route == "GRAPH":
            answer = self._graph_answer(question)
        else:
            answer = self._direct_answer(question)

        # Save to memory
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
        """Run through GraphCypherQAChain."""
        # Inject chat history into the question for context
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
        """Answer directly from LLM with memory context."""
        history = self._history_text()
        system = (
            "You are a helpful data dictionary assistant. "
            "Answer clearly and concisely."
        )
        messages = [SystemMessage(content=system)]
        if history:
            messages.append(HumanMessage(content=f"Conversation so far:\n{history}"))
        messages.append(HumanMessage(content=question))

        return self.llm.invoke(messages).content

    def _history_text(self) -> str:
        msgs = self.memory.messages[-20:]  # last 10 turns = 20 messages
        if not msgs:
            return ""
        lines = []
        for m in msgs:
            role = "User" if isinstance(m, HumanMessage) else "Assistant"
            lines.append(f"{role}: {m.content}")
        return "\n".join(lines)
