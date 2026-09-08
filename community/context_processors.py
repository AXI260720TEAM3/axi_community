"""
사이드바에 항상 필요한 값을 모든 템플릿에 자동으로 넣어줍니다.

각 뷰에서 게시판 목록이나 안 읽은 쪽지 수를 넘길 필요가 없습니다.
settings.py 의 TEMPLATES > OPTIONS > context_processors 에 등록되어 있습니다.

넣어주는 값
    nav_boards    사이드바 게시판 목록 (Board 전체)
    unread_count  로그인한 사람이 안 읽은 쪽지 수

현재 메뉴 표시(aria-current)는 각 뷰에서 nav_current 로 넘깁니다.
    게시판  -> board_id 숫자
    그 외    -> 'qna' / 'message' / 'mypage'
"""

from .models import Board, Message


def sidebar(request):
    unread = 0
    if request.user.is_authenticated:
        unread = Message.objects.filter(
            receiver=request.user, read_at__isnull=True
        ).count()

    return {
        "nav_boards": Board.objects.all().order_by("board_id"),
        "unread_count": unread,
    }
