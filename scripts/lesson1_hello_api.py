import time

from fastapi import FastAPI

app = FastAPI(title="hello")


@app.get("/fast")
async def fast() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/slow-bad")
async def slow_bad() -> dict[str, str]:
    time.sleep(8)  # blocks the whole event loop
    return {"status": "done"}


@app.get("/slow-good")
def slow_good() -> dict[str, str]:
    time.sleep(8)  # plain def: FastAPI runs it in a worker thread
    return {"status": "done"}
