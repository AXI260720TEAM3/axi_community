"""
[C] 쪽지

읽음 여부는 별도 컬럼이 아니라 read_at 이 비어 있는지로 판단합니다.
쪽지를 열어볼 때 read_at 에 현재 시각을 넣으세요. 사이드바의 안 읽은 개수가 줄어듭니다.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def message_box(request):
    # TODO [C] 받은 쪽지 / 보낸 쪽지 탭
    #          받은 쪽지  Message.objects.filter(receiver=request.user)
    #          보낸 쪽지  Message.objects.filter(sender=request.user)
    return render(request, "message/box.html", {"nav_current": "message"})


@login_required
def message_detail(request, message_id):
    # TODO [C] 받는 사람 본인인지 확인 → read_at = timezone.now() 로 읽음 처리
    return render(request, "message/box.html", {"nav_current": "message"})


@login_required
def message_send(request):
    # TODO [C] 받는 사람은 login_id 로 찾습니다. 자기 자신에게 보내지 못하게 막으세요.
    raise NotImplementedError("message_send — [C] 담당")
