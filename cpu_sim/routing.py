"""
WebSocket routing for cpu_sim app
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/cpu/$', consumers.CPUConsumer.as_asgi()),
]

