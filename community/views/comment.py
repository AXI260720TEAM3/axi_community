"""
[C] 댓글

Q&A 게시판에는 댓글을 달 수 없습니다. board.allow_comment 를 반드시 확인하세요.
삭제는 실제로 지우지 말고 is_deleted = True 로 표시합니다.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from ..models import Post, PostComment, Notification
from ..permissions import is_owner
from django.urls import reverse


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

            # 대댓글의 대댓글은 막고 1단계까지만 허용
            if parent.parent_id is not None:
                return redirect(
                    "post_detail",
                    post_id=post_id,
                )

        if content:
            comment = PostComment.objects.create(
        post=post,
        writer=request.user,
        parent=parent,
        content=content,
    )

    # 일반 댓글이면 게시글 작성자에게 알림
    if parent is None:
        Notification.notify(
    receiver=question.writer,
    kind=Notification.Kind.ANSWER,
    message=f"{request.user.member_name}님이 내 Q&A에 답변을 남겼습니다.",
    link=reverse(
        "qna_detail",
        args=[question.post_id],
    ),
    actor=request.user,
)

    # 대댓글이면 원댓글 작성자에게 알림
    else:
        Notification.notify(
            receiver=parent.writer,
            kind=Notification.Kind.COMMENT,
            message=f"{request.user.member_name}님이 내 댓글에 답글을 남겼습니다.",
            link=reverse("post_detail", args=[post.post_id],),
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
