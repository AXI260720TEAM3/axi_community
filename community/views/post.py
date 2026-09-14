"""
[A] 팀장 — 글쓰기 · 수정 · 삭제 · 첨부파일

post_detail 은 목록에서 제목을 눌렀을 때 화면이 뜨도록 읽기 기능만 채워두었습니다.
나머지는 뼈대만 있습니다.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from ..models import Attachment, Post, Board, PostLike
from ..permissions import is_owner, can_write, write_denied_reason
from django.utils import timezone

from django.contrib import messages

import logging
from django.http import FileResponse

from django.db.models import F



logger = logging.getLogger(__name__)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related("board", "writer"), pk=post_id, is_deleted=False
    )

    # 조회수: 한 번 본 글은 이 브라우저 세션이 끝날 때까지 다시 세지 않습니다.
    seen = request.session.setdefault("seen_posts", [])
    if post.post_id not in seen:
        Post.objects.filter(pk=post.post_id).update(view_count=F("view_count") + 1)
        post.view_count += 1
        seen.append(post.post_id)
        request.session.modified = True
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


# ---- 첨부파일 제한
# 실행 파일이나 너무 큰 파일이 올라가지 않게 막습니다.
MAX_UPLOAD_SIZE = 10 * 1024 * 1024          # 한 파일 10MB
ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".pdf", ".hwp", ".hwpx", ".doc", ".docx",
    ".xls", ".xlsx", ".ppt", ".pptx",
    ".txt", ".csv", ".md", ".sql", ".zip",
}


def attachment_error(files):
    """첨부가 규칙에 맞는지 봅니다. 문제가 있으면 사용자에게 보여줄 문구를, 없으면 None 을 돌려줍니다."""
    for f in files:
        ext = "." + f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""

        if ext not in ALLOWED_EXTENSIONS:
            return f"'{f.name}' 은(는) 올릴 수 없는 형식입니다. 이미지·문서·압축 파일만 올릴 수 있습니다."

        if f.size > MAX_UPLOAD_SIZE:
            return f"'{f.name}' 의 크기가 너무 큽니다. 한 파일에 10MB 까지 올릴 수 있습니다."

    return None


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

        files = request.FILES.getlist("files")
        error = attachment_error(files)

        if error:
            messages.error(request, error, extra_tags="alert")
            return render(request, "board/form.html",
                          {"board":board,"title":title,"content":content})

        post = Post.objects.create(
            board=board,
            writer=request.user,
            title=title,
            content=content,
        )
        for f in files:
            Attachment.objects.create(
                post=post,
                origin_name=f.name,
                stored_path=f,
                file_size=f.size,
            )
        return redirect("post_detail",post_id=post.post_id)
    
    return render(request, "board/form.html",{"board": board})


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

        files = request.FILES.getlist("files")
        error = attachment_error(files)

        if error:
            messages.error(request, error, extra_tags="alert")
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
        for f in files:
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
        if a.post.board.board_name == "Q&A":
            return redirect("qna_detail", post_id=a.post.parent_id or a.post_id)
        return redirect("post_detail", post_id=a.post_id)
    
    return FileResponse(f, as_attachment=True, filename=a.origin_name)

    # # TODO [A] FileResponse 로 내려주기. 다운로드 파일명은 origin_name 을 사용합니다.
    # raise NotImplementedError("attachment_download — [A] 팀장 담당")

@login_required
def post_like(request, post_id):
    """게시글 추천 / 추천 취소 토글 함수"""
    if request.method == "POST":
        post = get_object_or_404(Post, pk=post_id)

        # 1. 본인 작성 글 추천 불가 처리 (선택 사항)
        if post.writer == request.user:
            messages.error(request, "본인이 작성한 글은 추천할 수 없습니다.")
            return redirect('post_detail', post_id=post.post_id)

        # 2. 이미 추천했는지 확인
        like_qs = PostLike.objects.filter(member=request.user, post=post)

        if like_qs.exists():
            # 이미 눌렀으면 삭제 (추천 취소)
            like_qs.delete()
            messages.success(request, "추천을 취소했습니다.")
        else:
            # 안 눌렀으면 생성 (추천 등록)
            PostLike.objects.create(member=request.user, post=post)
            messages.success(request, "게시글을 추천했습니다.")

        return redirect('post_detail', post_id=post.post_id)

    return redirect('post_detail', post_id=post_id)