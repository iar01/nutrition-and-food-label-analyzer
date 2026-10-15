from dataclasses import dataclass
from typing import Any

import pytest
from labellens.agents.schemas import FinalSummary
from labellens.llm.structured import LLMFormatError, structured_call


@dataclass
class Reply:
    content: str


class ScriptedLLM:
    def __init__(self, replies: list[str]) -> None:
        self.replies = replies
        self.calls = 0

    def invoke(self, messages: list) -> Reply:
        reply = self.replies[min(self.calls, len(self.replies) - 1)]
        self.calls += 1
        return Reply(reply)


def test_valid_json_with_think_block_and_prose() -> Any:
    llm = ScriptedLLM(['<think>hmm</think> Sure! {"summary": "ok", "tips": []} Hope that helps'])
    assert structured_call(llm, FinalSummary, "sys", "user").summary == "ok"


def test_repair_loop_recovers() -> Any:
    llm = ScriptedLLM(["not json at all", '{"summary": "fixed"}'])
    assert structured_call(llm, FinalSummary, "sys", "user").summary == "fixed"
    assert llm.calls == 2


def test_gives_up_with_format_error() -> Any:
    llm = ScriptedLLM(["nope"])
    with pytest.raises(LLMFormatError):
        structured_call(llm, FinalSummary, "sys", "user")
