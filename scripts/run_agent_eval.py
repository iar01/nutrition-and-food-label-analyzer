import argparse
import random
from typing import Any

import duckdb
from labellens.agents.deps import Deps, build_default_deps
from labellens.agents.graph import build_graph
from labellens.agents.nodes.finish import BANNED
from labellens.agents.rules import ALLERGEN_TAG, DIET_FLAG
from labellens.config import settings
from labellens.llm.fake import FakeLLM
from langchain_core.messages import HumanMessage


def check(product: dict[str, Any], profile: dict[str, Any], out: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    v = out.get("verdicts")
    if not v:
        return ["no verdicts produced"]

    for allergen in profile["allergens"]:
        tag = ALLERGEN_TAG[allergen]
        status = v["allergens"][allergen]["status"]
        if tag in (product.get("allergens_tags") or []) and status != "contains":
            failures.append(f"{allergen} declared but status={status}")
        if tag in (product.get("traces_tags") or []) and status not in ("contains", "may_contain"):
            failures.append(f"{allergen} in traces but status={status}")

    for diet in profile["diets"]:
        flag = product.get(DIET_FLAG[diet])
        status = v["diets"][diet]["status"]
        if flag == "no" and status != "not_suitable":
            failures.append(f"{diet} flag=no but status={status}")
        if flag != "yes" and status == "suitable":
            failures.append(f"{diet} flag={flag} but status=suitable")

    if not out.get("answer"):
        failures.append("empty answer")
    if BANNED.search(out.get("draft", {}).get("summary", "")):
        failures.append("banned word in summary")
    return failures


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--fake-llm", action="store_true", help="fast run without the real model")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    deps = build_default_deps()
    if args.fake_llm:
        deps = Deps(
            llm=FakeLLM(),
            repo=deps.repo,
            searcher=deps.searcher,
            additive_cards=deps.additive_cards,
        )
    graph = build_graph(deps)

    con = duckdb.connect(str(settings.product_db_path), read_only=True)
    codes = [
        r[0] for r in con.execute(f"SELECT code FROM products USING SAMPLE {args.n}").fetchall()
    ]
    rng = random.Random(args.seed)

    total_failures = 0
    for code in codes:
        product = deps.repo.get(code)
        profile = {
            "diets": rng.sample(list(DIET_FLAG), 2),
            "allergens": rng.sample(list(ALLERGEN_TAG), 2),
            "goals": [],
        }
        out = graph.invoke(
            {
                "user_text": f"check {code}",
                "messages": [HumanMessage(content=f"check {code}")],
                "profile": profile,
                "auto_pick": True,
                "evidence": [],
                "findings": {},
                "revisions": 0,
                "error": None,
                "critic_feedback": None,
            }
        )
        failures = check(product, profile, out)
        total_failures += bool(failures)
        if failures:
            print(code, product.get("name"), profile, failures)

    print(f"\n{len(codes) - total_failures}/{len(codes)} products passed all invariants")


if __name__ == "__main__":
    main()
