from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator

from .models import Notification, NotificationTemplate


@login_required
def notification_list(request):
    filter_status = request.GET.get('status', '')
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('template').order_by('-created_at')

    if filter_status:
        notifications = notifications.filter(status=filter_status)

    unread_count = Notification.objects.filter(
        recipient=request.user, status__in=['pending', 'sent']
    ).count()

    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'title': 'Notifications',
        'notifications': page_obj,
        'unread_count': unread_count,
        'status_choices': Notification.NOTIFICATION_STATUS,
        'current_status': filter_status,
    }
    return render(request, 'notifications/notification_list.html', context)


@login_required
def notification_detail(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)

    if notification.status not in ('read', 'failed'):
        notification.status = 'read'
        notification.read_at = timezone.now()
        notification.save(update_fields=['status', 'read_at'])

    context = {
        'title': notification.subject,
        'notification': notification,
    }
    return render(request, 'notifications/notification_detail.html', context)


@login_required
def mark_all_read(request):
    if request.method == 'POST':
        Notification.objects.filter(
            recipient=request.user,
            status__in=['pending', 'sent']
        ).update(status='read', read_at=timezone.now())
        messages.success(request, 'All notifications marked as read.')
    return redirect('notifications:notification_list')


@login_required
def mark_read_ajax(request, pk):
    if request.method == 'POST':
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.status = 'read'
        notification.read_at = timezone.now()
        notification.save(update_fields=['status', 'read_at'])
        unread = Notification.objects.filter(
            recipient=request.user, status__in=['pending', 'sent']
        ).count()
        return JsonResponse({'success': True, 'unread_count': unread})
    return JsonResponse({'success': False}, status=405)


@login_required
def unread_count_api(request):
    count = Notification.objects.filter(
        recipient=request.user, status__in=['pending', 'sent']
    ).count()
    return JsonResponse({'unread_count': count})


@login_required
def delete_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    if request.method == 'POST':
        notification.delete()
        messages.success(request, 'Notification deleted.')
    return redirect('notifications:notification_list')


# ── Admin / staff only ────────────────────────────────

@login_required
def create_notification(request):
    if request.user.role != 'administrator':
        messages.error(request, 'Access denied.')
        return redirect('notifications:notification_list')

    from django.contrib.auth import get_user_model
    User = get_user_model()

    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        delivery_method = request.POST.get('delivery_method', 'in_app')
        template_id = request.POST.get('template_id')

        if not (recipient_id and subject and message):
            messages.error(request, 'Recipient, subject and message are required.')
        else:
            recipient = get_object_or_404(User, pk=recipient_id)
            template = None
            if template_id:
                template = get_object_or_404(NotificationTemplate, pk=template_id)

            Notification.objects.create(
                recipient=recipient,
                template=template,
                subject=subject,
                message=message,
                delivery_method=delivery_method,
                status='sent',
                sent_at=timezone.now(),
            )
            messages.success(request, f'Notification sent to {recipient.get_full_name()}.')
            return redirect('notifications:notification_list')

    users = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    templates = NotificationTemplate.objects.filter(is_active=True)
    context = {
        'title': 'Send Notification',
        'users': users,
        'templates': templates,
        'delivery_methods': Notification.DELIVERY_METHODS,
    }
    return render(request, 'notifications/create_notification.html', context)
