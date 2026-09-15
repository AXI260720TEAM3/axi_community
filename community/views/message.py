from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from ..models import Message, Notification


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
        receiver_deleted=False,
    ).count()

    if current_tab == "sent":
        messages_queryset = (
            Message.objects
            .filter(sender=request.user, sender_deleted=False)
            .select_related("receiver", "receiver__user_type")
            .order_by("-sent_at")
        )
    else:
        messages_queryset = (
            Message.objects
            .filter(receiver=request.user, receiver_deleted=False)
            .select_related("sender", "sender__user_type")
            .order_by("-sent_at")
        )

    message_page = Paginator(
        messages_queryset,
        MESSAGE_PAGE_SIZE,
    ).get_page(request.GET.get("page"))

    receiver_login_id = request.GET.get("receiver", "").strip()
    selected_receiver = None

    if receiver_login_id:
        selected_receiver = User.objects.filter(
            username=receiver_login_id,
        ).first()

        if selected_receiver is None:
            messages.error(
                request,
                "그런 아이디의 회원이 없습니다.",
            )

        elif selected_receiver == request.user:
            messages.error(
                request,
                "자기 자신에게는 쪽지를 보낼 수 없습니다.",
            )
            selected_receiver = None

    member_choices = (
        User.objects
        .exclude(pk=request.user.pk)
        .select_related("user_type")
        .order_by("member_name")
    )

    return render(
        request,
        "message/box.html",
        {
            "nav_current": "message",
            "message_page": message_page,
            "unread_count": unread_count,
            "current_tab": current_tab,
            "selected_receiver": selected_receiver,
            "member_choices": member_choices,
            "receiver_login_id": receiver_login_id,
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

    if (
        is_sender and message.sender_deleted
    ) or (
        is_receiver and message.receiver_deleted
    ):
        return redirect("message_box")

    if is_receiver and message.read_at is None:
        message.read_at = timezone.now()
        message.save(update_fields=["read_at"])

    can_edit_delete = is_sender and message.read_at is None

    if request.method == "POST":
        action = request.POST.get("action", "").strip()

        if action == "delete":
            message.delete_for(request.user)

            messages.success(
                request,
                "쪽지를 삭제했습니다.",
            )

            tab = "sent" if is_sender else "received"
            return redirect(
                f"{reverse('message_box')}?tab={tab}"
            )

        if not is_sender:
            messages.error(
                request,
                "받은 쪽지는 수정하거나 취소할 수 없습니다.",
            )
            return redirect(
                "message_detail",
                message_id=message.message_id,
            )

        if message.read_at is not None:
            messages.error(
                request,
                "상대방이 이미 읽은 쪽지는 수정하거나 취소할 수 없습니다.",
            )
            return redirect(
                "message_detail",
                message_id=message.message_id,
            )

        if action == "cancel":
            message_link = reverse(
                "message_detail",
                args=[message.message_id],
            )

            Notification.objects.filter(
                receiver=message.receiver,
                kind=Notification.Kind.MESSAGE,
                link=message_link,
            ).delete()

            message.delete()

            messages.success(
                request,
                "쪽지를 발송 취소했습니다.",
            )

            return redirect(
                f"{reverse('message_box')}?tab=sent"
            )

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


def _is_popup(request):
    return (
        request.headers.get("x-requested-with")
        == "XMLHttpRequest"
    )


def _send_failed(request, text):
    if _is_popup(request):
        return JsonResponse(
            {
                "ok": False,
                "error": text,
            },
            status=400,
        )

    messages.error(request, text)
    return redirect("message_box")


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
        return _send_failed(
            request,
            "받는 사람을 선택해주세요.",
        )

    if not content:
        return _send_failed(
            request,
            "쪽지 내용을 입력해주세요.",
        )

    receiver = User.objects.filter(
        username=receiver_login_id,
    ).first()

    if receiver is None:
        return _send_failed(
            request,
            "그런 아이디의 회원이 없습니다.",
        )

    if receiver == request.user:
        return _send_failed(
            request,
            "자기 자신에게는 쪽지를 보낼 수 없습니다.",
        )

    new_message = Message.objects.create(
        sender=request.user,
        receiver=receiver,
        content=content,
    )

    Notification.notify(
        receiver=receiver,
        kind=Notification.Kind.MESSAGE,
        message=f"{request.user.member_name}님이 새 쪽지를 보냈습니다.",
        link=reverse(
            "message_detail",
            args=[new_message.message_id],
        ),
        actor=request.user,
    )

    if _is_popup(request):
        return JsonResponse({"ok": True})

    messages.success(
        request,
        "쪽지를 보냈습니다.",
    )

    return redirect(
        f"{reverse('message_box')}?tab=sent"
    )