"""
[C] 댓글

Q&A 게시판에는 댓글을 달 수 없습니다. board.allow_comment 를 반드시 확인하세요.
삭제는 실제로 지우지 말고 is_deleted = True 로 표시합니다.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def comment_create(request, post_id):
    # TODO [C] post.board.allow_comment 확인 → PostComment 생성 → 원글로 redirect
    return redirect("post_detail", post_id=post_id)


@login_required
def comment_delete(request, comment_id):
    # TODO [C] 작성자 본인 확인(permissions.is_owner) → is_deleted = True
    raise NotImplementedError("comment_delete — [C] 담당")
