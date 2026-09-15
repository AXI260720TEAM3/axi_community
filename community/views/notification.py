from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import Notification


PAGE_SIZE = 10


@login_required
def notification_list(request):
    notifications = (
        Notification.objects
        .filter(receiver=request.user)
        .order_by("-created_at")
    )

    page = Paginator(
        notifications,
        PAGE_SIZE,
    ).get_page(request.GET.get("page"))

    return render(
        request,
        "notification/list.html",
        {
            "page": page,
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


@login_required
@require_POST
def notification_delete(request, notification_id):
    notification = get_object_or_404(
        Notification,
        notification_id=notification_id,
        receiver=request.user,
    )

    notification.delete()

    return redirect("notification_list")