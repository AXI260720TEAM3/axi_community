"""
[C] 쪽지

읽음 여부는 별도 컬럼이 아니라 read_at 이 비어 있는지로 판단합니다.
쪽지를 열어볼 때 read_at 에 현재 시각을 넣으세요. 사이드바의 안 읽은 개수가 줄어듭니다.
"""

"""
[C] 쪽지
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..models import Message


User = get_user_model()

MESSAGE_PAGE_SIZE = 5


@login_required
def message_box(request):
    current_tab = request.GET.get("tab", "received")

    if current_tab not in ("received", "sent"):
        current_tab = "received"

    unread_count = Message.objects.filter(
        receiver=request.user,
        read_at__isnull=True,
    ).count()

    if current_tab == "sent":
        messages_queryset = (
            Message.objects
            .filter(sender=request.user)
            .select_related("receiver", "receiver__user_type")
            .order_by("-sent_at")
        )
    else:
        messages_queryset = (
            Message.objects
            .filter(receiver=request.user)
            .select_related("sender", "sender__user_type")
            .order_by("-sent_at")
        )

    message_page = Paginator(
        messages_queryset,
        MESSAGE_PAGE_SIZE,
    ).get_page(request.GET.get("page"))

    receiver_login_id = request.GET.get(
        "receiver",
        "",
    ).strip()

    selected_receiver = None

    if receiver_login_id:
        selected_receiver = get_object_or_404(
            User,
            username=receiver_login_id,
        )

        if selected_receiver == request.user:
            messages.error(
                request,
                "자기 자신에게는 쪽지를 보낼 수 없습니다.",
            )
            selected_receiver = None

    return render(
        request,
        "message/box.html",
        {
            "nav_current": "message",
            "message_page": message_page,
            "unread_count": unread_count,
            "current_tab": current_tab,
            "selected_receiver": selected_receiver,
        },
    )


@login_required
def message_detail(request, message_id):
    message = get_object_or_404(
        Message.objects.select_related(
            "sender",
            "sender__user_type",
            "receiver",
            "receiver__user_type",
        ),
        pk=message_id,
    )

    is_sender = message.sender == request.user
    is_receiver = message.receiver == request.user

    if not is_sender and not is_receiver:
        return redirect("message_box")

    if is_receiver and message.read_at is None:
        message.read_at = timezone.now()
        message.save(update_fields=["read_at"])

    can_edit_delete = is_sender and message.read_at is None

    if request.method == "POST":
        if not is_sender:
            messages.error(
                request,
                "받은 쪽지는 수정하거나 삭제할 수 없습니다.",
            )
            return redirect(
                "message_detail",
                message_id=message.message_id,
            )

        if message.read_at is not None:
            messages.error(
                request,
                "상대방이 이미 읽은 쪽지는 수정하거나 삭제할 수 없습니다.",
            )
            return redirect(
                "message_detail",
                message_id=message.message_id,
            )

        action = request.POST.get("action", "").strip()

        if action == "edit":
            content = request.POST.get(
                "content",
                "",
            ).strip()

            if not content:
                messages.error(
                    request,
                    "쪽지 내용을 입력해주세요.",
                )
                return redirect(
                    "message_detail",
                    message_id=message.message_id,
                )

            message.content = content
            message.save(update_fields=["content"])

            messages.success(
                request,
                "쪽지를 수정했습니다.",
            )

            return redirect(
                "message_detail",
                message_id=message.message_id,
            )

        if action == "delete":
            message.delete()

            messages.success(
                request,
                "쪽지를 삭제했습니다.",
            )

            return redirect("message_box")

    return render(
        request,
        "message/detail.html",
        {
            "nav_current": "message",
            "message": message,
            "is_sender": is_sender,
            "is_receiver": is_receiver,
            "can_edit_delete": can_edit_delete,
        },
    )


@login_required
def message_send(request):
    if request.method != "POST":
        return redirect("message_box")

    receiver_login_id = request.POST.get(
        "receiver",
        "",
    ).strip()

    content = request.POST.get(
        "content",
        "",
    ).strip()

    if not receiver_login_id:
        messages.error(
            request,
            "받는 사람을 선택해주세요.",
        )
        return redirect("message_box")

    if not content:
        messages.error(
            request,
            "쪽지 내용을 입력해주세요.",
        )
        return redirect("message_box")

    receiver = get_object_or_404(
        User,
        username=receiver_login_id,
    )

    if receiver == request.user:
        messages.error(
            request,
            "자기 자신에게는 쪽지를 보낼 수 없습니다.",
        )
        return redirect("message_box")

    Message.objects.create(
        sender=request.user,
        receiver=receiver,
        content=content,
    )

    messages.success(
        request,
        "쪽지를 보냈습니다.",
    )

    return redirect("message_box")
