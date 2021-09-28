#!/bin/bash -l
nohup /usr/local/bin/uvicorn xiami_seckill_backend.asgi:websocket_application --host="0.0.0.0" --port=7366 --limit-concurrency 100 --reload &