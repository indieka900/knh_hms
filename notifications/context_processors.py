from .models import Notification


def notifications(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(
            recipient=request.user, status__in=['pending', 'sent']
        ).count()
        return {'unread_notifications': count}
    return {'unread_notifications': 0}
