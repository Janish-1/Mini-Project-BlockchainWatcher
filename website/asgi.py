"""
ASGI config for website project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

# import os

# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')

# application = get_asgi_application()

import os

from django.core.asgi import get_asgi_application

from django.urls import path
from channels.auth import AuthMiddlewareStack
from channels.routing import URLRouter, ProtocolTypeRouter
from crypto.consumers import UpdatePriceConsumer


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')

application = get_asgi_application()

wspatterns = [
    path('ws/price/', UpdatePriceConsumer),
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            wspatterns
        )
    )
})
