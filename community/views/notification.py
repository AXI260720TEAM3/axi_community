"""
[C] 알림

알림 목록 조회
알림 하나 읽음 처리
알림 전체 읽음 처리
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import Notification


@login_required
def notification_list(request):
    notifications = (
        Notification.objects
        .filter(receiver=request.user)
        .order_by("-created_at")
    )

    return render(
        request,
        "notification/list.html",
        {
            "notifications": notifications,
            "nav_current": "notification",
        },
    )


@login_required
@require_POST
def notification_read(request, notification_id):
    notification = get_object_or_404(
        Notification,
        notification_id=notification_id,
        receiver=request.user,
    )

    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])

    if notification.link:
        return redirect(notification.link)

    return redirect("notification_list")


@login_required
@require_POST
def notification_read_all(request):
    Notification.objects.filter(
        receiver=request.user,
        read_at__isnull=True,
    ).update(
        read_at=timezone.now(),
    )

    return redirect("notification_list")