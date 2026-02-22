import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from chat.kg_chat import KGChat

chat = KGChat(
    neo4j_uri=os.getenv("NEO4J_URI"),
    neo4j_user=os.getenv("NEO4J_USER"),
    neo4j_password=os.getenv("NEO4J_PASSWORD"),
    google_api_key=os.getenv("GEMINI_API_KEY"),
    model=os.getenv("GEMINI_MODEL"),
    debug=os.getenv("DEBUG", "").lower() == "true",
)

print("\n GraphRAG Chat — ask anything about your database schema")
print(" Type 'exit' to quit | 'reset' to clear memory\n")

while True:
    try:
        q = input("You: ").strip()
    except (KeyboardInterrupt, EOFError):
        break
    if not q:
        continue
    if q.lower() in ("exit", "quit"):
        break
    if q.lower() == "reset":
        chat.reset_memory()
        continue
    print(f"\nAssistant: {chat.ask(q)}\n")
