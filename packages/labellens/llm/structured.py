import json
import re
from typing import Any, TypeVar

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from labellens.config import settings

T = TypeVar("T", bound=BaseModel)
THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


class LLMFormatError(RuntimeError):
    """The model never produced valid JSON for the schema."""


def extract_json(raw: str) -> str:
    text = THINK_RE.sub("", raw).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON object found in the reply")
    return text[start : end + 1]


def structured_call[T: BaseModel](
    llm: Any, schema: type[T], system: str, user: str, retries: int = 1
) -> T:
    schema_text = json.dumps(schema.model_json_schema())
    if "qwen3" in settings.llm_model.lower():
        user = user + "\n/no_think"  # Qwen3: skip the long thinking phase

    messages: list[BaseMessage] = [
        SystemMessage(
            content=(
                f"{system}\n\nReply with ONLY a JSON object that matches this JSON schema. "
                f"No prose, no code fences.\n{schema_text}"
            )
        ),
        HumanMessage(content=user),
    ]

    last_error = ""
    for attempt in range(retries + 1):
        if attempt:
            messages.append(
                HumanMessage(
                    content=f"Your last reply was not valid ({last_error}). Reply again with ONLY the JSON object."
                )
            )
        raw = str(llm.invoke(messages).content)
        try:
            return schema.model_validate_json(extract_json(raw))
        except (ValidationError, ValueError) as exc:
            last_error = str(exc).replace("\n", " ")[:300]
    raise LLMFormatError(last_error)
