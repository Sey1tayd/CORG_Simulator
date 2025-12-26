"""
URL configuration for sim_django project.
"""
from django.urls import path, include

urlpatterns = [
    path('', include('cpu_sim.urls')),
]

