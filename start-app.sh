#!/usr/bin/env sh

opentelemetry-instrument \
    fastapi dev main.py --host=0.0.0.0 --port="$PORT"
