from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from ..models import Attachment, Board, BoardPermission, Notification, Post
from ..permissions import can_write
from .post import attachment_error


PAGE_SIZE = 10
QNA_BOARD_NAME = "Q&A"


def qna_list(request):
    board = get_object_or_404(Board, board_name=QNA_BOARD_NAME)
    keyword = request.GET.get("q", "").strip()

    answers_queryset = (
        Post.objects.visible()
        .select_related("writer", "writer__user_type")
        .order_by("created_at")
    )

    questions = (
        Post.objects.visible()
        .roots()
        .filter(board=board)
        .select_related("writer", "writer__user_type")
        .annotate(
            answer_count=Count(
                "answers",
                filter=Q(answers__is_deleted=False),
                distinct=True,
            ),
            file_count=Count("attachments", distinct=True),
        )
        .prefetch_related(
            Prefetch(
                "answers",
                queryset=answers_queryset,
                to_attr="visible_answers",
            )
        )
    )

    if keyword:
        questions = questions.filter(
            Q(title__icontains=keyword)
            | Q(content__icontains=keyword)
            | Q(
                answers__is_deleted=False,
                answers__title__icontains=keyword,
            )
            | Q(
                answers__is_deleted=False,
                answers__content__icontains=keyword,
            )
        ).distinct()

    questions = questions.order_by("-created_at")
    page = Paginator(
        questions,
        PAGE_SIZE,
    ).get_page(request.GET.get("page"))

    return render(request, "qna/list.html", {
        "board": board,
        "page": page,
        "keyword": keyword,
        "can_ask": can_write(
            request.user,
            board,
            BoardPermission.PermissionType.QUESTION,
        ),
        "nav_current": "qna",
    })


def qna_detail(request, post_id):
    question = get_object_or_404(
        Post.objects.visible()
        .roots()
        .select_related(
            "board",
            "writer",
            "writer__user_type",
        )
        .prefetch_related("attachments"),
        post_id=post_id,
        board__board_name=QNA_BOARD_NAME,
    )

    is_owner = (
        request.user.is_authenticated
        and question.writer_id == request.user.member_id
    )

    if request.method == "POST":
        if not is_owner:
            return redirect(
                "qna_detail",
                post_id=question.post_id,
            )

        action = request.POST.get("action", "").strip()

        if action == "delete":
            question.is_deleted = True
            question.save(update_fields=["is_deleted"])

            messages.success(
                request,
                "질문을 삭제했습니다.",
            )

            return redirect("qna_list")

    answers = (
        question.answers
        .filter(is_deleted=False)
        .select_related(
            "writer",
            "writer__user_type",
        )
        .prefetch_related("attachments")
        .order_by("created_at")
    )

    return render(request, "qna/detail.html", {
        "question": question,
        "answers": answers,
        "attachments": question.attachments.all(),
        "is_owner": is_owner,
        "can_answer": can_write(
            request.user,
            question.board,
            BoardPermission.PermissionType.ANSWER,
        ),
        "nav_current": "qna",
    })


@login_required
def qna_edit(request, post_id):
    question = get_object_or_404(
        Post.objects.visible()
        .roots()
        .select_related("board"),
        post_id=post_id,
        board__board_name=QNA_BOARD_NAME,
        writer=request.user,
    )

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()

        if not title or not content:
            messages.error(
                request,
                "제목과 내용을 모두 입력해주세요.",
            )

            return render(request, "qna/question_edit.html", {
                "question": question,
                "title": title,
                "content": content,
                "attachments": question.attachments.all(),
                "nav_current": "qna",
            })

        files = request.FILES.getlist("files")
        error = attachment_error(files)

        if error:
            messages.error(request, error)

            return render(request, "qna/question_edit.html", {
                "question": question,
                "title": title,
                "content": content,
                "attachments": question.attachments.all(),
                "nav_current": "qna",
            })

        question.title = title
        question.content = content
        question.save(
            update_fields=["title", "content"]
        )

        delete_files = request.POST.getlist("delete_files")

        if delete_files:
            Attachment.objects.filter(
                post=question,
                attachment_id__in=delete_files,
            ).delete()

        for f in files:
            Attachment.objects.create(
                post=question,
                origin_name=f.name,
                stored_path=f,
                file_size=f.size,
            )

        messages.success(
            request,
            "질문을 수정했습니다.",
        )

        return redirect(
            "qna_detail",
            post_id=question.post_id,
        )

    return render(request, "qna/question_edit.html", {
        "question": question,
        "title": question.title,
        "content": question.content,
        "attachments": question.attachments.all(),
        "nav_current": "qna",
    })


@login_required
def qna_ask(request):
    board = get_object_or_404(
        Board,
        board_name=QNA_BOARD_NAME,
    )

    if not can_write(
        request.user,
        board,
        BoardPermission.PermissionType.QUESTION,
    ):
        return redirect("qna_list")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()

        # 첨부 검사는 일반 게시판(post.py)과 같은 규칙을 씁니다.
        # 글을 만들기 전에 봐야 첨부만 거부되고 글은 남는 일이 없습니다.
        files = request.FILES.getlist("files")
        error = attachment_error(files)

        if error:
            messages.error(request, error)

            return render(request, "qna/ask.html", {
                "board": board,
                "title": title,
                "content": content,
                "error": error,
                "nav_current": "qna",
            })

        if title and content:
            question = Post.objects.create(
                board=board,
                writer=request.user,
                title=title,
                content=content,
            )

            for f in files:
                Attachment.objects.create(
                    post=question,
                    origin_name=f.name,
                    stored_path=f,
                    file_size=f.size,
                )

            return redirect(
                "qna_detail",
                post_id=question.post_id,
            )

        # ask.html 에는 error 를 그리는 자리가 없습니다. messages 로도 함께 알립니다.
        messages.error(request, "제목과 내용을 모두 입력해주세요.")

        return render(request, "qna/ask.html", {
            "board": board,
            "title": title,
            "content": content,
            "error": "제목과 내용을 모두 입력해주세요.",
            "nav_current": "qna",
        })

    return render(request, "qna/ask.html", {
        "board": board,
        "nav_current": "qna",
    })


@login_required
def qna_answer(request, post_id):
    question = get_object_or_404(
        Post.objects.visible()
        .roots()
        .select_related("board"),
        post_id=post_id,
        board__board_name=QNA_BOARD_NAME,
    )

    if not can_write(
        request.user,
        question.board,
        BoardPermission.PermissionType.ANSWER,
    ):
        return redirect(
            "qna_detail",
            post_id=question.post_id,
        )

    if request.method == "POST":
        existing_answer = Post.objects.filter(
            parent=question,
            writer=request.user,
            is_deleted=False,
        ).exists()

        if existing_answer:
            messages.error(
                request,
                "이미 이 질문에 답변을 작성했습니다.",
            )

            return redirect(
                "qna_detail",
                post_id=question.post_id,
            )

        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()

        files = request.FILES.getlist("files")
        error = attachment_error(files)

        if error:
            messages.error(request, error)

            return redirect(
                "qna_detail",
                post_id=question.post_id,
            )

        if title and content:
            answer = Post.objects.create(
                board=question.board,
                writer=request.user,
                parent=question,
                title=title,
                content=content,
            )

            for f in files:
                Attachment.objects.create(
                    post=answer,
                    origin_name=f.name,
                    stored_path=f,
                    file_size=f.size,
                )

            Notification.notify(
                receiver=question.writer,
                kind=Notification.Kind.ANSWER,
                message=(
                    f"{request.user.member_name}님이 "
                    "내 Q&A에 답변을 남겼습니다."
                ),
                link=reverse(
                    "qna_detail",
                    args=[question.post_id],
                ),
                actor=request.user,
            )

        return redirect(
            "qna_detail",
            post_id=question.post_id,
        )

    return redirect(
        "qna_detail",
        post_id=question.post_id,
    )


@login_required
@require_POST
def qna_accept_answer(request, post_id, answer_id):
    question = get_object_or_404(
        Post.objects.visible().roots(),
        post_id=post_id,
        board__board_name=QNA_BOARD_NAME,
    )

    if question.writer_id != request.user.member_id:
        messages.error(
            request,
            "질문 작성자만 답변을 채택할 수 있습니다.",
        )

        return redirect(
            "qna_detail",
            post_id=question.post_id,
        )

    answer = get_object_or_404(
        Post.objects.visible(),
        post_id=answer_id,
        parent=question,
    )

    if question.accepted_answer_id is not None:
        messages.error(
            request,
            "이미 채택된 답변이 있습니다.",
        )

        return redirect(
            "qna_detail",
            post_id=question.post_id,
        )

    question.accepted_answer = answer
    question.save(
        update_fields=["accepted_answer"]
    )

    # ---------------------------------------------------------
    # [추가] 답변 채택 알림 발송
    # ---------------------------------------------------------
    if answer.writer != request.user:
        Notification.notify(
            receiver=answer.writer,
            kind=Notification.Kind.ANSWER,  # 또는 모델에 상수가 정의되어 있다면 적절한 종류로 지정
            message=(
                f"작성하신 답변이 '{question.title}' 질문에서 채택되었습니다."
            ),
            link=reverse(
                "qna_detail",
                args=[question.post_id],
            ),
            actor=request.user,
        )

    messages.success(
        request,
        "답변을 채택했습니다.",
    )

    return redirect(
        "qna_detail",
        post_id=question.post_id,
    )


@login_required
def qna_edit_answer(request, post_id, answer_id):
    question = get_object_or_404(
        Post.objects.visible().roots(),
        post_id=post_id,
        board__board_name=QNA_BOARD_NAME,
    )

    answer = get_object_or_404(
        Post.objects.visible(),
        post_id=answer_id,
        parent=question,
        writer=request.user,
    )

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()

        if not title or not content:
            messages.error(
                request,
                "제목과 내용을 모두 입력해주세요.",
            )

            return render(request, "qna/answer_edit.html", {
                "question": question,
                "answer": answer,
                "title": title,
                "content": content,
                "attachments": answer.attachments.all(),
                "nav_current": "qna",
            })

        files = request.FILES.getlist("files")
        error = attachment_error(files)

        if error:
            messages.error(request, error)

            return render(request, "qna/answer_edit.html", {
                "question": question,
                "answer": answer,
                "title": title,
                "content": content,
                "attachments": answer.attachments.all(),
                "nav_current": "qna",
            })

        answer.title = title
        answer.content = content
        answer.save(
            update_fields=["title", "content"]
        )

        delete_files = request.POST.getlist("delete_files")

        if delete_files:
            Attachment.objects.filter(
                post=answer,
                attachment_id__in=delete_files,
            ).delete()

        for f in files:
            Attachment.objects.create(
                post=answer,
                origin_name=f.name,
                stored_path=f,
                file_size=f.size,
            )

        messages.success(
            request,
            "답변을 수정했습니다.",
        )

        return redirect(
            "qna_detail",
            post_id=question.post_id,
        )

    return render(request, "qna/answer_edit.html", {
        "question": question,
        "answer": answer,
        "title": answer.title,
        "content": answer.content,
        "attachments": answer.attachments.all(),
        "nav_current": "qna",
    })


@login_required
@require_POST
def qna_delete_answer(request, post_id, answer_id):
    question = get_object_or_404(
        Post.objects.visible().roots(),
        post_id=post_id,
        board__board_name=QNA_BOARD_NAME,
    )

    answer = get_object_or_404(
        Post.objects.visible(),
        post_id=answer_id,
        parent=question,
        writer=request.user,
    )

    if question.accepted_answer_id == answer.post_id:
        messages.error(
            request,
            "채택된 답변은 삭제할 수 없습니다.",
        )

        return redirect(
            "qna_detail",
            post_id=question.post_id,
        )

    answer.is_deleted = True
    answer.save(
        update_fields=["is_deleted"]
    )

    messages.success(
        request,
        "답변을 삭제했습니다.",
    )

    return redirect(
        "qna_detail",
        post_id=question.post_id,
    )