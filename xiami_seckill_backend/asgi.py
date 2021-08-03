"""
ASGI config for xiami_seckill_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xiami_seckill_backend.settings')
django.setup()
application = get_asgi_application()

from .src.websocket.websocket_handler import BackendWebSocketConsumer

backend_websocket_consumer = BackendWebSocketConsumer()

async def websocket_application(scope, receive, send):
    if scope['type'] == 'http':
        await application(scope, receive, send)
    elif scope['type'] == 'websocket':
        await backend_websocket_consumer.handle_request(scope, receive, send)
    else:
        raise NotImplementedError(f"Unknown scope type {scope['type']}")