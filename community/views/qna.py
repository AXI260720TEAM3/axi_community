"""
[C] Q&A 질문과 답변

답변은 별도 테이블이 아니라 Post 의 자기참조입니다.
    질문  parent 가 비어 있음
    답변  parent 에 질문 Post 를 가리킴  (post.answers 로 역참조)

작성 권한은 permissions.can_write 로 확인합니다. 코드에 유형을 박지 마세요.
    수강생  질문만        멘토  질문과 답변        강사  답변만
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..models import Board, BoardPermission, Post
from ..permissions import can_write


def qna_list(request):
    # TODO [C] 질문 목록 + 각 질문의 답변 수. 답변 없는 질문을 구분해서 보여주면 좋습니다.
    #          board.py 의 board_list 를 참고하면 검색·페이지네이션을 그대로 쓸 수 있습니다.
    return render(request, "qna/list.html", {"nav_current": "qna"})


def qna_detail(request, post_id):
    # TODO [C] 질문 + 딸린 답변들(post.answers.filter(is_deleted=False))
    return render(request, "qna/list.html", {"nav_current": "qna"})


@login_required
def qna_ask(request):
    # TODO [C] can_write(user, board, PermissionType.QUESTION) 확인 후 질문 등록
    raise NotImplementedError("qna_ask — [C] 담당")


@login_required
def qna_answer(request, post_id):
    # TODO [C] can_write(user, board, PermissionType.ANSWER) 확인
    #          Post 를 만들고 parent 에 질문을 넣습니다. board 는 질문과 같은 Q&A 입니다.
    raise NotImplementedError("qna_answer — [C] 담당")
