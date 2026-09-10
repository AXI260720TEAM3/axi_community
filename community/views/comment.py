"""
[C] 댓글

Q&A 게시판에는 댓글을 달 수 없습니다. board.allow_comment 를 반드시 확인하세요.
삭제는 실제로 지우지 말고 is_deleted = True 로 표시합니다.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from ..models import Post, PostComment
from ..permissions import is_owner


@login_required
def comment_create(request, post_id):
    post = get_object_or_404(
        Post,
        post_id=post_id,
        is_deleted=False,
    )

    if not post.board.allow_comment:
        return redirect("post_detail", post_id=post_id)

    if request.method == "POST":
        content = request.POST.get("content", "").strip()

        if content:
            PostComment.objects.create(
                post=post,
                writer=request.user,
                content=content,
            )

    return redirect("post_detail", post_id=post_id)


@login_required
def comment_delete(request, comment_id):
    comment = get_object_or_404(
        PostComment,
        comment_id=comment_id,
        is_deleted=False,
    )

    post_id = comment.post_id

    if is_owner(request.user, comment):
        comment.is_deleted = True
        comment.save(update_fields=["is_deleted"])

    return redirect("post_detail", post_id=post_id)
