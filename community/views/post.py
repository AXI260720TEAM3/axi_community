"""
[A] 팀장 — 글쓰기 · 수정 · 삭제 · 첨부파일

post_detail 은 목록에서 제목을 눌렀을 때 화면이 뜨도록 읽기 기능만 채워두었습니다.
나머지는 뼈대만 있습니다.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from ..models import Attachment, Post
from ..permissions import is_owner


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related("board", "writer"), pk=post_id, is_deleted=False
    )
    return render(
        request,
        "board/detail.html",
        {
            "post": post,
            "comments": post.comments.filter(is_deleted=False).select_related("writer"),
            "attachments": post.attachments.all(),
            "is_owner": is_owner(request.user, post),
            "nav_current": post.board_id,
        },
    )


@login_required
def post_create(request, board_id):
    # TODO [A] 작성 권한 확인(permissions.can_write) → 폼 검증 → 저장 → 첨부파일 처리
    #          첨부파일은 request.FILES.getlist('files') 로 여러 개를 받습니다.
    #          form 태그에 enctype="multipart/form-data" 가 없으면 파일이 안 넘어옵니다.
    raise NotImplementedError("post_create — [A] 팀장 담당")


@login_required
def post_update(request, post_id):
    # TODO [A] 작성자 본인인지 확인(permissions.is_owner) → 수정 → updated_at 갱신
    raise NotImplementedError("post_update — [A] 팀장 담당")


@login_required
def post_delete(request, post_id):
    # TODO [A] 실제로 지우지 말고 is_deleted = True 로 표시(삭제 플래그)
    raise NotImplementedError("post_delete — [A] 팀장 담당")


def attachment_download(request, attachment_id):
    # TODO [A] FileResponse 로 내려주기. 다운로드 파일명은 origin_name 을 사용합니다.
    raise NotImplementedError("attachment_download — [A] 팀장 담당")
