import logging
import re
import uuid
from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import StreamingResponse
from langgraph.types import Command
from pydantic import ValidationError
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool

from labellens.api.config import ApiConfig
from labellens.api.errors import ApiError
from labellens.api.logging_setup import request_id_var
from labellens.api.runner import (
    cached_chat_events,
    chat_events,
    followup_state,
    initial_state,
    semantic_cached_chat_events,
    to_analysis,
)
from labellens.api.schemas import (
    AnalysisOut,
    AnalyzeResponse,
    CandidateOut,
    ChatRequest,
    ErrorOut,
    Profile,
)
from labellens.api.security import guard
from labellens.api.services import Services, get_services
from labellens.api.slots import RunSlots
from labellens.api.uploads import clean_image, read_limited

logger = logging.getLogger("labellens.api")
router = APIRouter(prefix="/v1", tags=["analysis"], dependencies=[Depends(guard)])


def parse_profile(raw: str) -> Profile:
    try:
        return Profile.model_validate_json(raw or "{}")
    except ValidationError as exc:
        raise ApiError(
            422,
            "invalid_profile",
            'profile must be JSON such as {"diets": ["vegan"], "allergens": ["milk"]}.',
        ) from exc


async def identify_by_image(
    services: Services, upload: UploadFile, max_bytes: int
) -> list[dict[str, Any]]:
    if services.get_clip is None:
        raise ApiError(501, "image_search_disabled", "Image search is not enabled on this server.")
    clip_loader = services.get_clip
    raw = await read_limited(upload, max_bytes)
    image = clean_image(raw)

    def work() -> list[dict[str, Any]]:
        vector = clip_loader().embed_images([image])[0].tolist()
        return list(services.deps.searcher.by_image(vector, 5))

    hits = await run_in_threadpool(work)
    if not hits:
        raise ApiError(404, "no_match", "No similar product found for that image.")
    return hits


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    responses={
        404: {"model": ErrorOut},
        413: {"model": ErrorOut},
        415: {"model": ErrorOut},
        503: {"model": ErrorOut},
    },
)
async def analyze(
    request: Request,
    services: Annotated[Services, Depends(get_services)],
    barcode: Annotated[str | None, Form(pattern=r"^\d{8,14}$")] = None,
    text: Annotated[str | None, Form(min_length=2, max_length=300)] = None,
    profile: Annotated[str, Form(max_length=2000)] = "{}",
    image: Annotated[UploadFile | None, File()] = None,
) -> AnalyzeResponse:
    """Analyse one product from a barcode, a text query or a photo.

    Priority: barcode, then image, then text. For text queries the first match is used and the
    other matches are returned in `candidates`.
    """
    if not (barcode or text or image):
        raise ApiError(422, "no_input", "Send a barcode, a text query or an image.")
    prof = parse_profile(profile)
    config: ApiConfig = request.app.state.config

    candidates: list[CandidateOut] = []
    if barcode:
        cached = services.analysis_cache.get(barcode, prof.model_dump())
        if cached is not None:
            return AnalyzeResponse(
                **cached.model_dump(),
                matched_by="barcode",
                candidates=[],
                thread_id=str(uuid.uuid4()),
                request_id=request_id_var.get(),
            )
        matched_by = "barcode"
        user_text = f"check {barcode}"
    elif image is not None:
        matched_by = "image"
        hits = await identify_by_image(services, image, config.max_upload_bytes)
        candidates = [CandidateOut(**h) for h in hits]
        user_text = f"check {hits[0]['code']}"
    else:
        matched_by = "text"
        user_text = text or ""

    thread_id = str(uuid.uuid4())
    graph_config = {"configurable": {"thread_id": thread_id}}
    inputs = initial_state(user_text, prof.model_dump(), auto_pick=True)

    slots: RunSlots = request.app.state.run_slots
    async with slots.slot():
        values = await run_in_threadpool(services.graph.invoke, inputs, graph_config)

    if values.get("error") or not values.get("product"):
        raise ApiError(
            404, values.get("error") or "not_found", values.get("answer") or "Product not found."
        )

    analysis = to_analysis(values)
    if values.get("product", {}).get("code"):
        services.analysis_cache.set(values["product"]["code"], prof.model_dump(), analysis)

    return AnalyzeResponse(
        **analysis.model_dump(),
        matched_by=matched_by,  # type: ignore[arg-type]
        candidates=candidates,
        thread_id=thread_id,
        request_id=request_id_var.get(),
    )


@router.post(
    "/chat",
    responses={
        200: {
            "model": AnalysisOut,
            "content": {"text/event-stream": {}},
            "description": "Server-Sent Events stream.",
        },
        409: {"model": ErrorOut},
        503: {"model": ErrorOut},
    },
)
async def chat(
    body: ChatRequest,
    request: Request,
    services: Annotated[Services, Depends(get_services)],
) -> StreamingResponse:
    """Run the agent and stream progress as Server-Sent Events."""
    # Fast path: check instant cache for barcode queries in chat
    if body.message is not None:
        barcode_match = re.search(r"\b\d{8,14}\b", body.message)
        if barcode_match:
            barcode = barcode_match.group(0)
            cached = services.analysis_cache.get(barcode, body.profile.model_dump())
            if cached is not None:
                thread_id = str(uuid.uuid4())

                async def cached_stream() -> AsyncIterator[str]:
                    for part in cached_chat_events(thread_id, cached):
                        yield part

                return StreamingResponse(
                    cached_stream(),
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
                )

            # Fast path: Tier 2 Semantic Cache
            embedder = getattr(getattr(services.deps, "searcher", None), "text_emb", None)
            if embedder is not None:
                sem_hit = services.semantic_cache.get(
                    query=body.message,
                    product_code=barcode,
                    profile=body.profile.model_dump(),
                    embedder=embedder,
                )
                if sem_hit is not None:
                    thread_id = str(uuid.uuid4())

                    async def sem_stream() -> AsyncIterator[str]:
                        for part in semantic_cached_chat_events(thread_id, sem_hit):
                            yield part

                    return StreamingResponse(
                        sem_stream(),
                        media_type="text/event-stream",
                        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
                    )

    graph = services.graph
    inputs: Any
    if body.message is not None:
        if body.thread_id:
            thread_id = str(body.thread_id)
            config = {"configurable": {"thread_id": thread_id}}
            existing_state = await run_in_threadpool(graph.get_state, config)
            if existing_state and existing_state.values.get("product"):
                inputs = followup_state(body.message, body.profile.model_dump())
            else:
                inputs = initial_state(
                    body.message, body.profile.model_dump(), bool(body.auto_pick)
                )
        else:
            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}
            inputs = initial_state(body.message, body.profile.model_dump(), bool(body.auto_pick))
    else:
        thread_id = str(body.thread_id)
        config = {"configurable": {"thread_id": thread_id}}
        state = await run_in_threadpool(graph.get_state, config)
        if not state.next:
            raise ApiError(409, "nothing_to_resume", "That thread is not waiting for a choice.")
        inputs = Command(resume={"code": body.resume_code})

    slots: RunSlots = request.app.state.run_slots
    await slots.acquire()  # raises 503 if every slot is busy

    embedder = getattr(getattr(services.deps, "searcher", None), "text_emb", None)

    async def stream() -> AsyncIterator[str]:
        try:
            async for part in iterate_in_threadpool(
                chat_events(
                    graph,
                    inputs,
                    config,
                    thread_id,
                    cache=services.analysis_cache,
                    semantic_cache=services.semantic_cache,
                    embedder=embedder,
                )
            ):
                yield part
        finally:
            slots.release()  # also runs if the client disconnects

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
