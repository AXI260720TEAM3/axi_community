from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Attachment, Board, BoardPermission, Post
from ..permissions import can_write


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
            file_count=Count(
                "attachments",
                distinct=True,
            ),
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
            | Q(answers__is_deleted=False, answers__title__icontains=keyword)
            | Q(answers__is_deleted=False, answers__content__icontains=keyword)
        ).distinct()

    questions = questions.order_by("-created_at")

    page = Paginator(
        questions,
        PAGE_SIZE,
    ).get_page(request.GET.get("page"))

    return render(
        request,
        "qna/list.html",
        {
            "board": board,
            "page": page,
            "keyword": keyword,
            "can_ask": can_write(
                request.user,
                board,
                BoardPermission.PermissionType.QUESTION,
            ),
            "nav_current": "qna",
        },
    )


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

        if action == "edit":
            title = request.POST.get("title", "").strip()
            content = request.POST.get("content", "").strip()

            if not title or not content:
                messages.error(
                    request,
                    "제목과 내용을 모두 입력해주세요.",
                )
                return redirect(
                    "qna_detail",
                    post_id=question.post_id,
                )

            question.title = title
            question.content = content
            question.save(
                update_fields=[
                    "title",
                    "content",
                ]
            )

            messages.success(
                request,
                "질문을 수정했습니다.",
            )

            return redirect(
                "qna_detail",
                post_id=question.post_id,
            )

        if action == "delete":
            question.is_deleted = True
            question.save(
                update_fields=["is_deleted"]
            )

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

    return render(
        request,
        "qna/detail.html",
        {
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
        },
    )


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
        title = request.POST.get(
            "title",
            "",
        ).strip()

        content = request.POST.get(
            "content",
            "",
        ).strip()

        if title and content:
            question = Post.objects.create(
                board=board,
                writer=request.user,
                title=title,
                content=content,
            )

            for f in request.FILES.getlist("files"):
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

        return render(
            request,
            "qna/ask.html",
            {
                "board": board,
                "title": title,
                "content": content,
                "error": "제목과 내용을 모두 입력해주세요.",
                "nav_current": "qna",
            },
        )

    return render(
        request,
        "qna/ask.html",
        {
            "board": board,
            "nav_current": "qna",
        },
    )


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
        title = request.POST.get(
            "title",
            "",
        ).strip()

        content = request.POST.get(
            "content",
            "",
        ).strip()

        if title and content:
            Post.objects.create(
                board=question.board,
                writer=request.user,
                parent=question,
                title=title,
                content=content,
            )

        return redirect(
            "qna_detail",
            post_id=question.post_id,
        )

    return redirect(
        "qna_detail",
        post_id=question.post_id,
    )
