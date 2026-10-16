import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi import Path as PathParam
from fastapi.responses import FileResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

from labellens.agents.types import Allergen, Diet, Grade
from labellens.api.errors import ApiError
from labellens.api.runner import to_product_summary
from labellens.api.schemas import (
    CheckResult,
    ErrorOut,
    FeedbackIn,
    FeedbackOut,
    ProductSummary,
    ReadyOut,
    SearchHit,
    SearchResponse,
)
from labellens.api.security import guard
from labellens.api.services import Services, get_services
from labellens.config import settings

logger = logging.getLogger("labellens.api")

public = APIRouter(tags=["ops"])  # no API key
v1 = APIRouter(prefix="/v1", dependencies=[Depends(guard)])


@public.get("/health", response_model=dict[str, str])
async def health() -> dict[str, str]:
    """Liveness: the process is up."""
    return {"status": "ok"}


@public.get("/ready", response_model=ReadyOut, responses={503: {"model": ReadyOut}})
async def ready(services: Annotated[Services, Depends(get_services)]) -> JSONResponse:
    """Readiness: can the service do its job? Critical failures give 503, others give 'degraded'."""
    results: list[CheckResult] = []
    for check in services.checks:
        try:
            ok = bool(await run_in_threadpool(check.fn))
        except Exception:
            logger.warning("readiness check failed: %s", check.name, exc_info=True)
            ok = False
        results.append(CheckResult(name=check.name, ok=ok, critical=check.critical))

    critical_ok = all(r.ok for r in results if r.critical)
    if all(r.ok for r in results):
        status = "ok"
    elif critical_ok:
        status = "degraded"
    else:
        status = "unavailable"
    body = ReadyOut(status=status, checks=results)  # type: ignore[arg-type]
    return JSONResponse(body.model_dump(), status_code=200 if critical_ok else 503)


@v1.get(
    "/products/{code}",
    response_model=ProductSummary,
    tags=["products"],
    responses={404: {"model": ErrorOut}},
)
async def get_product(
    code: Annotated[str, PathParam(pattern=r"^\d{8,14}$", description="Barcode, 8 to 14 digits.")],
    services: Annotated[Services, Depends(get_services)],
) -> ProductSummary:
    product = await run_in_threadpool(services.get_product, code)
    if product is None and len(code) < 13:
        product = await run_in_threadpool(services.get_product, code.zfill(13))
    if product is None:
        raise ApiError(404, "not_found", "No product with that barcode in the data.")
    return to_product_summary(product)


@v1.get(
    "/products/{code}/image",
    response_class=FileResponse,
    response_model=None,
    tags=["products"],
    responses={404: {"model": ErrorOut}},
)
async def product_image(
    code: Annotated[str, PathParam(pattern=r"^\d{8,14}$", description="Barcode, 8 to 14 digits.")],
) -> FileResponse:
    """The product photo downloaded in Phase 4, if we have one."""
    path = settings.images_dir / f"{code}.jpg"  # the pattern guarantees digits only: no path tricks
    if not path.is_file():
        raise ApiError(404, "no_image", "No image for that product.")
    return FileResponse(
        path, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=86400"}
    )


@v1.get("/search", response_model=SearchResponse, tags=["products"])
async def search(
    services: Annotated[Services, Depends(get_services)],
    q: Annotated[
        str, Query(min_length=2, max_length=200, description="Product name, brand or description.")
    ],
    limit: Annotated[int, Query(ge=1, le=10)] = 5,
    diet: Annotated[list[Diet] | None, Query()] = None,
    exclude_allergen: Annotated[list[Allergen] | None, Query()] = None,
    nutriscore: Annotated[list[Grade] | None, Query()] = None,
    category: Annotated[str | None, Query(max_length=100)] = None,
) -> SearchResponse:
    filters = {
        "diets": diet,
        "exclude_allergens": exclude_allergen,
        "nutriscore_in": nutriscore,
        "category": category,
    }
    hits = await run_in_threadpool(services.deps.searcher.products, q, limit, filters)
    return SearchResponse(count=len(hits), results=[SearchHit(**h) for h in hits])


@v1.post("/feedback", response_model=FeedbackOut, status_code=201, tags=["feedback"])
async def feedback(
    body: FeedbackIn,
    services: Annotated[Services, Depends(get_services)],
) -> FeedbackOut:
    """Store a thumbs up or down for an earlier answer."""
    feedback_id = await run_in_threadpool(
        services.feedback.add,
        body.rating,
        body.comment,
        body.request_id,
        body.thread_id,
        body.product_code,
    )
    return FeedbackOut(id=feedback_id)
