"""
작성 권한 판정 — 팀장이 관리합니다.

board_permission 테이블에 있는 조합만 허용됩니다.
없는 조합은 자동으로 금지입니다. 코드에 게시판 이름을 박아넣지 마세요.

    공지사항   직원만 일반글
    자유게시판 수강생·강사·멘토·직원 모두 일반글
    Q&A        수강생 질문 / 멘토 질문·답변 / 강사 답변
    취업정보   강사·멘토·직원 일반글
"""

from .models import BoardPermission


def can_write(user, board, permission_type=BoardPermission.PermissionType.GENERAL):
    """user 가 board 에 permission_type 으로 글을 쓸 수 있는지"""
    if not user.is_authenticated:
        return False
    return BoardPermission.objects.filter(
        board=board,
        user_type_id=user.user_type_id,
        permission_type=permission_type,
    ).exists()


def write_denied_reason(board):
    """글쓰기 버튼 대신 보여줄 안내 문구"""
    names = (
        BoardPermission.objects.filter(
            board=board,
            permission_type=BoardPermission.PermissionType.GENERAL,
        )
        .values_list("user_type__type_name", flat=True)
        .distinct()
    )
    if not names:
        return f"{board.board_name}은(는) 글을 쓸 수 없습니다."
    return f"{board.board_name}은(는) {'·'.join(names)}만 쓸 수 있습니다."


def is_owner(user, obj):
    """글이나 댓글의 작성자 본인인지. 수정·삭제 확인에 사용하세요."""
    return user.is_authenticated and obj.writer_id == user.member_id
