"""
[C] 댓글

Q&A 게시판에는 댓글을 달 수 없습니다. board.allow_comment 를 반드시 확인하세요.
삭제는 실제로 지우지 말고 is_deleted = True 로 표시합니다.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from ..models import Notification, Post, PostComment
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
        parent_id = request.POST.get("parent_id", "").strip()

        parent = None

        if parent_id:
            parent = get_object_or_404(
                PostComment,
                comment_id=parent_id,
                post=post,
                is_deleted=False,
            )

            if parent.parent_id is not None:
                return redirect(
                    "post_detail",
                    post_id=post_id,
                )

        if content:
            PostComment.objects.create(
                post=post,
                writer=request.user,
                parent=parent,
                content=content,
            )

            if parent is None:
                Notification.notify(
                    receiver=post.writer,
                    kind=Notification.Kind.COMMENT,
                    message=f"{request.user.member_name}님이 내 게시글에 댓글을 남겼습니다.",
                    link=reverse(
                        "post_detail",
                        args=[post.post_id],
                    ),
                    actor=request.user,
                )
            else:
                Notification.notify(
                    receiver=parent.writer,
                    kind=Notification.Kind.COMMENT,
                    message=f"{request.user.member_name}님이 내 댓글에 답글을 남겼습니다.",
                    link=reverse(
                        "post_detail",
                        args=[post.post_id],
                    ),
                    actor=request.user,
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

@login_required
def comment_update(request, comment_id):
    comment = get_object_or_404(
        PostComment,
        comment_id=comment_id,
        is_deleted=False,
    )

    # 작성자 본인만 수정 가능
    if is_owner(request.user, comment):
        if request.method == "POST":
            content = request.POST.get("content", "").strip()
            if content:
                comment.content = content
                comment.save(update_fields=["content"])

    return redirect("post_detail", post_id=comment.post_id)