import asyncio
import logging
from typing import Any

import httpx
import orjson
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from pythonjsonlogger import jsonlogger


app = FastAPI()
# FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()


def json_dumps(data, *args, **kwargs) -> str:
    return orjson.dumps(data).decode("utf-8")


def configure_logging():
    # LoggingInstrumentor(log_level="DEBUG").instrument(set_logging_format=True)
    logging.basicConfig()
    root_logger = logging.getLogger()

    basic_fields = [
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "module",
        "message",
        "name",
        "pathname",
        "process",
        "processName",
        "threadName"
    ]
    otel_fields = [
        "otelSpanID",
        "otelTraceID",
        "otelTraceSampled",
        "otelServiceName",
    ]
    fields = " ".join(f"%({field})s" for field in (basic_fields + otel_fields))

    log_handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fields,
        json_serializer=json_dumps,
        timestamp=True,
    )
    log_handler.setFormatter(formatter)
    root_logger.handlers[0] = log_handler


configure_logging()


logger = logging.getLogger("test")
tracer = trace.get_tracer(__name__)


@app.get("/")
async def root():
    logger.info("Hello, world!")
    with tracer.start_as_current_span("root") as span:
        span.set_attribute("foo", "bar")
        return {"Hello": "World"}


@app.get("/external")
async def external(url: str) -> dict[str, Any]:
    logger.info("Let's try an external URL...")
    with tracer.start_as_current_span("calling-external") as span:
        span.set_attribute("url", url)
        async with httpx.AsyncClient() as client:
            response = await client.get(url)

    return response.json()


@app.get("/slow/{amount}")
async def slow(amount: int) -> dict[str, Any]:
    with tracer.start_as_current_span("sleeping") as span:
        span.set_attribute("sleep-time", amount)
        await asyncio.sleep(amount)

    return {"slept": amount}


@app.get("/crash")
async def crash() -> str:
    with tracer.start_as_current_span("crashing"):
        raise RuntimeError("Let's crash!")
