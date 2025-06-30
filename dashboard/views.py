from django.shortcuts import render


def dashboard_view(request):
    """Render the dashboard view"""
    return render(request, 'dashboard.html', {
        'title': 'Dashboard'
    })

# Create your views here.
