"""
[C] Q&A 질문과 답변

답변은 별도 테이블이 아니라 Post 의 자기참조입니다.
    질문  parent 가 비어 있음
    답변  parent 에 질문 Post 를 가리킴  (post.answers 로 역참조)

작성 권한은 permissions.can_write 로 확인합니다. 코드에 유형을 박지 마세요.
    수강생  질문만        멘토  질문과 답변        강사  답변만
"""

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Board, BoardPermission, Post
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
            )
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

    page = Paginator(questions, PAGE_SIZE).get_page(request.GET.get("page"))

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
        .select_related("board", "writer", "writer__user_type"),
        post_id=post_id,
        board__board_name=QNA_BOARD_NAME,
    )

    answers = (
        question.answers.filter(is_deleted=False)
        .select_related("writer", "writer__user_type")
        .order_by("created_at")
    )

    return render(
        request,
        "qna/detail.html",
        {
            "question": question,
            "answers": answers,
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
    board = get_object_or_404(Board, board_name=QNA_BOARD_NAME)

    if not can_write(
        request.user,
        board,
        BoardPermission.PermissionType.QUESTION,
    ):
        return redirect("qna_list")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()

        if title and content:
            question = Post.objects.create(
                board=board,
                writer=request.user,
                title=title,
                content=content,
            )
            return redirect("qna_detail", post_id=question.post_id)

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
        return redirect("qna_detail", post_id=question.post_id)

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()

        if title and content:
            Post.objects.create(
                board=question.board,
                writer=request.user,
                parent=question,
                title=title,
                content=content,
            )

        return redirect("qna_detail", post_id=question.post_id)

    return redirect("qna_detail", post_id=question.post_id)
