import argparse
import sqlite3
import uuid
from typing import Any

from dotenv import load_dotenv
from labellens.agents.deps import build_default_deps
from labellens.agents.graph import build_graph
from labellens.config import settings
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command


def run(graph: Any, inputs: Any, config: dict[str, Any]) -> dict[str, Any] | None:
    """Stream node-by-node progress. Returns the interrupt payload if paused."""
    for chunk in graph.stream(inputs, config, stream_mode="updates"):
        for node, _update in chunk.items():
            if node == "__interrupt__":
                interrupts: Any = chunk["__interrupt__"]
                if not interrupts:
                    return None

                value: Any = interrupts[0].value
                if isinstance(value, dict):
                    return value

                raise TypeError(
                    f"Expected interrupt payload to be a dict, got {type(value).__name__}"
                )

            print(f"  [{node}] done")

    return None


def main() -> None:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("text", help="a question, a product name or a barcode")
    ap.add_argument(
        "--diet",
        action="append",
        default=[],
        help="vegan, vegetarian, gluten_free, lactose_free, palm_oil_free, nut_free",
    )
    ap.add_argument(
        "--allergen",
        action="append",
        default=[],
        help="milk, eggs, peanuts, nuts, soy, gluten, fish, ...",
    )
    ap.add_argument("--goal", action="append", default=[], help="low_sugar, low_salt, low_sat_fat")
    ap.add_argument(
        "--auto-pick", action="store_true", help="do not ask which product, take the first match"
    )
    ap.add_argument(
        "--thread", default=None, help="thread id (reuse it to continue a conversation)"
    )
    args = ap.parse_args()

    settings.checkpoint_db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(settings.checkpoint_db_path), check_same_thread=False)
    graph = build_graph(build_default_deps(), SqliteSaver(conn))

    thread_id = args.thread or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    print("thread:", thread_id)

    inputs: Any = {
        "user_text": args.text,
        "messages": [HumanMessage(content=args.text)],
        "profile": {"diets": args.diet, "allergens": args.allergen, "goals": args.goal},
        "auto_pick": args.auto_pick,
        "evidence": [],
        "findings": {},
        "revisions": 0,
        "error": None,
        "critic_feedback": None,
    }

    pending = run(graph, inputs, config)
    while pending:
        print("\n" + pending["question"])
        for i, c in enumerate(pending["candidates"], 1):
            print(f"  {i}. {c['name']} | {c['brands']} | {c['code']}")
        choice = int(input("Number: ")) - 1
        pending = run(
            graph, Command(resume={"code": pending["candidates"][choice]["code"]}), config
        )

    print("\n" + (graph.get_state(config).values.get("answer") or "(no answer)"))


if __name__ == "__main__":
    main()
