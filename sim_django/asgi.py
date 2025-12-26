"""
ASGI config for sim_django project.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import cpu_sim.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sim_django.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(
        cpu_sim.routing.websocket_urlpatterns
    ),
})

