"""
[A] 팀장 — 글쓰기 · 수정 · 삭제 · 첨부파일

post_detail 은 목록에서 제목을 눌렀을 때 화면이 뜨도록 읽기 기능만 채워두었습니다.
나머지는 뼈대만 있습니다.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from ..models import Attachment, Post, Board
from ..permissions import is_owner, can_write, write_denied_reason
from django.utils import timezone

from django.contrib import messages

import logging
from django.http import FileResponse

logger = logging.getLogger(__name__)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related("board", "writer"), pk=post_id, is_deleted=False
    )
    return render(
        request,
        "board/detail.html",
        {
            "post": post,
            "comments": post.comments.filter(is_deleted=False).select_related("writer"),
            "attachments": post.attachments.all(),
            "is_owner": is_owner(request.user, post),
            "nav_current": post.board_id,
        },
    )


@login_required
def post_create(request, board_id):
    board = get_object_or_404(Board, pk=board_id)

    if not can_write(request.user, board):
        messages.error(request, write_denied_reason(board), extra_tags="alert")
        return redirect("board_list", board_id=board.board_id)

    if request.method == "POST":
        # print("FILES:", request.FILES.getlist("files"))
        title = request.POST.get("title","").strip()
        content = request.POST.get("content","").strip()
        # print(request.POST)

        if not title or not content:
            messages.error(request,"제목과 내용을 모두 입력하세요.", extra_tags="alert")
            return render(request, "board/form.html",
                          {"board":board,"title":title,"content":content})

        post = Post.objects.create(
            board=board,
            writer=request.user,
            title=title,
            content=content,
        )
        for f in request.FILES.getlist("files"):
            Attachment.objects.create(
                post=post,
                origin_name=f.name,
                stored_path=f,
                file_size=f.size,
            )
        return redirect("post_detail",post_id=post.post_id)
    
    return render(request, "board/form.html",{"board": board})
    # TODO [A] 작성 권한 확인(permissions.can_write) → 폼 검증 → 저장 → 첨부파일 처리
    #          첨부파일은 request.FILES.getlist('files') 로 여러 개를 받습니다.
    #          form 태그에 enctype="multipart/form-data" 가 없으면 파일이 안 넘어옵니다.
    # raise NotImplementedError("post_create — [A] 팀장 담당")


@login_required
def post_update(request, post_id):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)

    if not is_owner(request.user, post):
        return redirect("post_detail", post_id=post.post_id)

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()

        if not title or not content:
            messages.error(request, "제목과 내용을 모두 입력하세요.", extra_tags="alert")
            return render(request, "board/edit.html", {
                "post": post,
                "title": title,
                "content": content,
                "attachments": post.attachments.all(),
                "nav_current": post.board_id,
            })

        post.title = title
        post.content = content
        post.updated_at = timezone.now()
        post.save()

        # 체크한 기존 첨부 삭제 — 반드시 이 글의 첨부 중에서만 찾습니다
        delete_ids = request.POST.getlist("delete_files")
        for a in post.attachments.filter(pk__in=delete_ids):
            a.stored_path.delete(save=False)   # 디스크의 실제 파일
            a.delete()                         # DB 의 행

        # 새로 추가한 첨부 저장 — 글쓰기와 같은 코드
        for f in request.FILES.getlist("files"):
            Attachment.objects.create(
                post=post,
                origin_name=f.name,
                stored_path=f,
                file_size=f.size,
            )
        return redirect("post_detail", post_id=post.post_id)

    return render(request, "board/edit.html", {
        "post": post,
        "title": post.title,
        "content": post.content,
        "attachments": post.attachments.all(),
        "nav_current": post.board_id,
    })

    # TODO [A] 작성자 본인인지 확인(permissions.is_owner) → 수정 → updated_at 갱신
    #raise NotImplementedError("post_update — [A] 팀장 담당")


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)

    if not is_owner(request.user, post):
        return redirect("post_detail", post_id=post.post_id)

    if request.method == "POST":
        post.is_deleted = True
        post.save()
        return redirect("board_list", board_id=post.board_id)
    
    return redirect("post_detail", post_id=post.post_id)

    # TODO [A] 실제로 지우지 말고 is_deleted = True 로 표시(삭제 플래그)
    # raise NotImplementedError("post_delete — [A] 팀장 담당")


def attachment_download(request, attachment_id):
    a = get_object_or_404(Attachment, pk=attachment_id, post__is_deleted=False)

    try:
        f = a.stored_path.open("rb")
    except FileNotFoundError:
        logger.warning("첨부파일 없음: id=%s path=%s", a.attachment_id, a.stored_path.name)
        messages.error(request, "파일을 찾을 수 없습니다. 관리자에게 문의하세요.", extra_tags="alert")
        return redirect("post_detail", post_id=a.post_id)
    
    return FileResponse(f, as_attachment=True, filename=a.origin_name)

    # # TODO [A] FileResponse 로 내려주기. 다운로드 파일명은 origin_name 을 사용합니다.
    # raise NotImplementedError("attachment_download — [A] 팀장 담당")
