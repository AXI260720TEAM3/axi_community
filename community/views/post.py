"""
[A] 팀장 — 글쓰기 · 수정 · 삭제 · 첨부파일

글쓰기·수정·삭제·첨부 다운로드·추천까지 모두 동작합니다.
Q&A 글은 화면이 따로 있어서 post_detail 에서 qna_detail 로 넘깁니다.
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

# 조회수 중복 집계를 막으려고 세션에 남겨두는 게시글 수
SEEN_LIMIT = 50


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related("board", "writer"), pk=post_id, is_deleted=False
    )

    # Q&A 는 화면 구조가 달라서 qna_detail 이 따로 담당합니다. [C]
    # 답변글은 자기 화면이 없으므로 원 질문으로 보냅니다.
    # 조회수를 올리기 전에 빠져나가야 넘어간 화면과 숫자가 어긋나지 않습니다.
    if post.board.is_qna:
        return redirect("qna_detail", post_id=post.parent_id or post.post_id)

    # 조회수: 한 번 본 글은 이 브라우저 세션이 끝날 때까지 다시 세지 않습니다.
    # 세션에 최근 SEEN_LIMIT 개만 남깁니다. 다 쌓으면 세션이 계속 불어납니다.
    # 그보다 더 많이 돌아본 뒤 옛 글로 되돌아가면 조회수가 한 번 더 오릅니다. 그 정도는 감수합니다.
    seen = request.session.get("seen_posts", [])
    if post.post_id not in seen:
        Post.objects.filter(pk=post.post_id).update(view_count=F("view_count") + 1)
        post.view_count += 1
        seen.append(post.post_id)
        request.session["seen_posts"] = seen[-SEEN_LIMIT:]
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
                          {"board":board,"title":title,"content":content,
                           "nav_current":board.board_id})

        files = request.FILES.getlist("files")
        error = attachment_error(files)

        if error:
            messages.error(request, error, extra_tags="alert")
            return render(request, "board/form.html",
                          {"board":board,"title":title,"content":content,
                           "nav_current":board.board_id})

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
    
    return render(request, "board/form.html",
                  {"board": board, "nav_current": board.board_id})


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


def attachment_download(request, attachment_id):
    a = get_object_or_404(Attachment, pk=attachment_id, post__is_deleted=False)

    try:
        f = a.stored_path.open("rb")
    except FileNotFoundError:
        logger.warning("첨부파일 없음: id=%s path=%s", a.attachment_id, a.stored_path.name)
        messages.error(request, "파일을 찾을 수 없습니다. 관리자에게 문의하세요.", extra_tags="alert")
        if a.post.board.is_qna:
            return redirect("qna_detail", post_id=a.post.parent_id or a.post_id)
        return redirect("post_detail", post_id=a.post_id)
    
    return FileResponse(f, as_attachment=True, filename=a.origin_name)

@login_required
def post_like(request, post_id):
  """게시글 / Q&A 질문 / 답변 추천 및 추천 취소 토글 함수"""
  # 삭제된 글은 상세 화면이 404 라서, 여기도 같이 막아야 추천수만 오르는 일이 없습니다
  post = get_object_or_404(Post, pk=post_id, is_deleted=False)

  # [리다이렉트 목적지 계산 함수]
  def get_redirect_response():
    # Q&A 게시판의 글인 경우
    if post.board and post.board.is_qna:
      # 답변글(parent가 있음)을 추천했으면 원본 질문 ID로, 질문글이면 본인 ID로 이동
      target_q_id = post.parent_id if post.parent_id else post.post_id
      return redirect("qna_detail", post_id=target_q_id)

    # 일반 게시판 글인 경우
    return redirect("post_detail", post_id=post.post_id)

  if request.method == "POST":
    # 1. 본인 작성 글 추천 불가 처리
    if post.writer == request.user:
      messages.error(request, "본인이 작성한 글은 추천할 수 없습니다.")
      return get_redirect_response()

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

    return get_redirect_response()

  return get_redirect_response()