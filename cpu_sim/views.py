"""
Views for cpu_sim app
"""
from django.shortcuts import render


def index(request):
    """Main CPU simulator page"""
    return render(request, 'cpu_sim/index.html')

