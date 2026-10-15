import sqlite3
import sys

from labellens.agents.deps import build_default_deps
from labellens.agents.graph import build_graph
from labellens.config import settings
from langgraph.checkpoint.sqlite import SqliteSaver

thread_id = sys.argv[1]
conn = sqlite3.connect(str(settings.checkpoint_db_path), check_same_thread=False)
graph = build_graph(build_default_deps(), SqliteSaver(conn))
state = graph.get_state({"configurable": {"thread_id": thread_id}})
print("next nodes:", state.next)
print("keys in state:", sorted(state.values))
print("overall:", (state.values.get("verdicts") or {}).get("overall"))
