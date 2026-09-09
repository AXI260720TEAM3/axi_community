"""
[B] 마이페이지

회원정보 수정은 signup 에서 만든 폼을 재사용할 수 있습니다.
내가 쓴 글은 Post.objects.visible().filter(writer=request.user) 로 가져옵니다.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from community.models import Post, Board  # 프로젝트 내 모델명에 맞춰 import


@login_required
def mypage(request):
    # TODO [B] 내 정보 + 내가 쓴 글 + 내가 쓴 댓글 + 받은 쪽지 요약
    return render(request, "acoount/index.html", {"nav_current": "mypage"})


@login_required
def profile_edit(request):
    # TODO [B] 이름·이메일·전화번호·주소 수정. 비밀번호 변경은 set_password() 사용
    return render(request, "mypage/index.html", {"nav_current": "mypage"})
