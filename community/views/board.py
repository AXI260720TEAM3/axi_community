"""
[A] 팀장 — 게시판 목록 · 검색 · 페이지네이션

다른 화면을 만들 때 참고할 수 있게 이 파일은 실제로 동작하도록 채워두었습니다.
검색은 Q 객체, 페이지 나누기는 Paginator 를 씁니다.
"""

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from ..models import QNA_BOARD_NAME, Board, Member, Post
from ..permissions import can_write, write_denied_reason

PAGE_SIZE = 10


def home(request):
    """첫 화면. 게시판별 최근 글과 요약을 모아 보여줍니다."""
    boards = {b.board_name: b for b in Board.objects.all()}

    def recent(board_name, limit=5):
        board = boards.get(board_name)
        if board is None:
            return []
        return list(
            Post.objects.visible().roots()
            .filter(board=board)
            .select_related("writer", "writer__user_type")
            .order_by("-created_at")[:limit]
        )

    # 템플릿에서 그대로 반복할 수 있게 블록 목록으로 만들어 둡니다
    sections = [
        {"title": name, "board": boards.get(name), "posts": recent(name)}
        for name in ("공지사항", "자유게시판", "취업정보", "멘토의 취업비밀")
    ]

    qna_board = boards.get(QNA_BOARD_NAME)
    waiting = []
    if qna_board:
        waiting = list(
            Post.objects.visible().roots()
            .filter(board=qna_board, accepted_answer__isnull=True)
            .annotate(answer_count=Count("answers", filter=Q(answers__is_deleted=False)))
            .filter(answer_count=0)
            .select_related("writer")
            .order_by("-created_at")[:5]
        )

    popular = list(
        Post.objects.visible().roots()
        .exclude(board__board_name=QNA_BOARD_NAME)
        .select_related("board", "writer")
        .annotate(like_count=Count("likes", distinct=True))
        .filter(like_count__gt=0)
        .order_by("-like_count", "-post_id")[:5]
    )

    return render(
        request,
        "home.html",
        {
            "sections": sections,
            "waiting": waiting,
            "popular": popular,
            "total_posts": Post.objects.visible().roots().count(),
            "total_members": Member.objects.filter(is_active=True).count(),
            "nav_current": "home",
        },
    )


def board_list(request, board_id):
    board = get_object_or_404(Board, pk=board_id)

    # Q&A 는 화면 구조가 달라서 따로 관리합니다. [C] 담당
    if board.is_qna:
        return redirect("qna_list")

    keyword = request.GET.get("q", "").strip()
    search_type = request.GET.get("type","all")

    # 익명 게시판에서 작성자 검색을 허용하면 이름으로 글쓴이를 특정할 수 있어 익명성이 깨집니다
    if board.is_anonymous or search_type not in ("all", "writer"):
        search_type = "all"

    # like_count 카운팅을 쿼리셋 annotate()에 추가
    posts = (
        Post.objects.visible()
        .roots()
        .filter(board=board)
        .select_related("writer", "writer__user_type")
        .annotate(
            comment_count=Count(
                "comments", filter=Q(comments__is_deleted=False), distinct=True
            ),
            file_count=Count("attachments", distinct=True),
            like_count=Count("likes", distinct=True),  # <-- 추천수 집계 추가
        )
    )

    if keyword:
        if search_type == "writer":
            posts = posts.filter(writer__member_name__icontains=keyword)
        else:
            posts = posts.filter(Q(title__icontains=keyword) | Q(content__icontains=keyword))

    # 화면에 보여줄 이름 : 실제 정렬 기준
    SORT_OPTIONS = {
        "new": ("최신순", "-created_at"),
        "view": ("조회순", "-view_count"),
        "like": ("추천순", "-like_count"),
        "title": ("제목순", "title"),
    }

    sort = request.GET.get("sort", "new")
    if sort not in SORT_OPTIONS:
        sort = "new"
    
    # annotate() 가 GROUP BY 를 붙이면 Meta.ordering 이 무효가 됩니다.
    # 정렬을 명시하지 않으면 페이지마다 순서가 달라질 수 있습니다.
    # 같은 값이 여러 개일 때 순서가 흔들리지 않게 항상 post_id 를 보조 기준으로 둡니다
    posts = posts.order_by(SORT_OPTIONS[sort][1], "-post_id")

    paginator = Paginator(posts, PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))

    # 글이 쌓여도 번호가 줄줄이 늘어나지 않게 현재 쪽 주변만 보여줍니다.
    # 사이에 낀 구간은 Paginator.ELLIPSIS('…') 로 나옵니다.
    page_range = paginator.get_elided_page_range(page.number, on_each_side=2, on_ends=1)

    return render(
        request,
        "board/list.html",
        {
            "board": board,
            "page": page,
            "keyword": keyword,
            "search_type": search_type,
            "can_write": can_write(request.user, board),
            "denied_reason": write_denied_reason(board),
            "nav_current": board.board_id,
            "sort": sort,
            "sort_options": SORT_OPTIONS,
            "page_range": page_range,
            "ellipsis": Paginator.ELLIPSIS,
        },
    )
