"""
[C] 쪽지

읽음 여부는 별도 컬럼이 아니라 read_at 이 비어 있는지로 판단합니다.
쪽지를 열어볼 때 read_at 에 현재 시각을 넣으세요. 사이드바의 안 읽은 개수가 줄어듭니다.
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..models import Message


User = get_user_model()


@login_required
def message_box(request):
    """
    받은 쪽지 / 보낸 쪽지를 보여주는 화면입니다.

    또한 게시글이나 댓글에서 사용자의 이름을 클릭하여
    쪽지를 보내는 경우를 지원합니다.

    예:
        /messages/?receiver=user123

    위와 같이 receiver가 URL 파라미터로 전달되면
    해당 사용자를 찾아서 쪽지 보내기 화면의
    '받는 사람'으로 미리 선택합니다.
    """

    received_messages = (
        Message.objects
        .filter(receiver=request.user)
        .select_related("sender")
        .order_by("-sent_at")
    )

    sent_messages = (
        Message.objects
        .filter(sender=request.user)
        .select_related("receiver")
        .order_by("-sent_at")
    )

    unread_count = Message.objects.filter(
        receiver=request.user,
        read_at__isnull=True,
    ).count()

    current_tab = request.GET.get(
        "tab",
        "received",
    )

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
            "received_messages": received_messages,
            "sent_messages": sent_messages,
            "unread_count": unread_count,
            "current_tab": current_tab,
            "selected_receiver": selected_receiver,
        },
    )


@login_required
def message_detail(request, message_id):
    """
    쪽지 하나를 상세하게 보여줍니다.

    받은 쪽지를 처음 열었을 때
    read_at에 현재 시간을 저장하여 읽음 처리합니다.

    보낸 사람 또는 받은 사람 본인만
    해당 쪽지를 볼 수 있습니다.
    """

    message = get_object_or_404(
        Message,
        pk=message_id,
    )

    if message.receiver == request.user:
        if message.read_at is None:
            message.read_at = timezone.now()
            message.save(
                update_fields=["read_at"]
            )

    elif message.sender == request.user:
        pass

    else:
        return redirect("message_box")

    return render(
        request,
        "message/detail.html",
        {
            "nav_current": "message",
            "message": message,
        },
    )


@login_required
def message_send(request):
    """
    쪽지를 보내는 기능입니다.

    받는 사람은 두 가지 방법으로 지정할 수 있습니다.

    1. 게시글/댓글의 사용자 이름을 클릭
       -> message_box에서 받는 사람을 미리 선택
       -> box.html의 form에서 receiver 값을 POST

    2. 쪽지함에서 직접 받는 사람의 login_id 입력
       -> receiver 값을 POST

    views.py에서는 Member 모델의 Django 필드명인
    username을 사용합니다.
    """

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
