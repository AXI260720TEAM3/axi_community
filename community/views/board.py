"""
[A] 팀장 — 게시판 목록 · 검색 · 페이지네이션

다른 화면을 만들 때 참고할 수 있게 이 파일은 실제로 동작하도록 채워두었습니다.
검색은 Q 객체, 페이지 나누기는 Paginator 를 씁니다.
"""

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Board, Post
from ..permissions import can_write, write_denied_reason

PAGE_SIZE = 10


def home(request):
    """첫 화면. 자유게시판으로 보냅니다."""
    free = Board.objects.filter(board_name="자유게시판").first()
    if free:
        return redirect("board_list", board_id=free.board_id)
    return redirect("board_list", board_id=1)


def board_list(request, board_id):
    board = get_object_or_404(Board, pk=board_id)

    # Q&A 는 화면 구조가 달라서 따로 관리합니다. [C] 담당
    if board.board_name == "Q&A":
        return redirect("qna_list")

    keyword = request.GET.get("q", "").strip()

    posts = (
        Post.objects.visible()
        .roots()
        .filter(board=board)
        .select_related("writer")
        .annotate(
            comment_count=Count(
                "comments", filter=Q(comments__is_deleted=False), distinct=True
            ),
            file_count=Count("attachments", distinct=True),
        )
    )

    if keyword:
        posts = posts.filter(Q(title__icontains=keyword) | Q(content__icontains=keyword))

    # annotate() 가 GROUP BY 를 붙이면 Meta.ordering 이 무효가 됩니다.
    # 정렬을 명시하지 않으면 페이지마다 순서가 달라질 수 있습니다.
    posts = posts.order_by("-created_at")

    page = Paginator(posts, PAGE_SIZE).get_page(request.GET.get("page"))

    return render(
        request,
        "board/list.html",
        {
            "board": board,
            "page": page,
            "keyword": keyword,
            "can_write": can_write(request.user, board),
            "denied_reason": write_denied_reason(board),
            "nav_current": board.board_id,
        },
    )
