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
from django.http import JsonResponse

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

def _is_popup(request):
    """팝업(fetch)에서 온 요청인지. 팝업 JS가 이 헤더를 붙여 보냅니다"""
    return request.headers.get("x-requested-with") == "XMLHttpRequest"

def _send_failed(request,text):
    """보내기 실패 응답. 팝업이면 JSON, 일반 폼이면 지금처럼 쪽지함으로."""
    if _is_popup(request):
        return JsonResponse({"ok":False, "error": text}, status=400)
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
        return _send_failed(request, "받는 사람을 선택해주세요.")

    if not content:
        return _send_failed(request, "쪽지 내용을 입력해주세요.")

    receiver = User.objects.filter(username=receiver_login_id).first()

    if receiver is None:
        return _send_failed(request, "그런 아이디의 회원이 없습니다.")

    if receiver == request.user:
        return _send_failed(request, "자기 자신에게는 쪽지를 보낼 수 없습니다.")

    Message.objects.create(
        sender=request.user,
        receiver=receiver,
        content=content,
    )

    if _is_popup(request):
        return JsonResponse({"ok": True})
    
    messages.success(
        request,
        "쪽지를 보냈습니다.",
    )

    return redirect("message_box")
