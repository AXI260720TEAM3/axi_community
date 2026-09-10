"""
URL 설계 — 팀장이 관리합니다.

** URL 이름(name=)은 이미 확정된 것입니다. 마음대로 바꾸지 마세요. **
각자 템플릿에서 {% url '이름' %} 으로 자유롭게 참조하면 됩니다.
새 화면이 필요하면 팀장에게 요청하세요.

담당 표시
    [A] 팀장  게시판 · 글쓰기 · 첨부파일
    [B]       회원가입 · 로그인 · 계정찾기 · 마이페이지
    [C]       댓글 · Q&A · 쪽지
"""

from django.urls import path

from .views import account, board, comment, message, mypage, post, qna

urlpatterns = [
    # ---------------------------------------------------------------- [A] 게시판
    path("", board.home, name="home"),
    path("boards/<int:board_id>/", board.board_list, name="board_list"),

    # ---------------------------------------------------------------- [A] 게시글
    path("boards/<int:board_id>/write/", post.post_create, name="post_create"),
    path("posts/<int:post_id>/", post.post_detail, name="post_detail"),
    path("posts/<int:post_id>/edit/", post.post_update, name="post_update"),
    path("posts/<int:post_id>/delete/", post.post_delete, name="post_delete"),
    path("attachments/<int:attachment_id>/", post.attachment_download, name="attachment_download"),

    # ---------------------------------------------------------------- [B] 계정
    path("accounts/login/", account.login_view, name="login"),
    path("accounts/logout/", account.logout_view, name="logout"),
    path("accounts/signup/", account.signup, name="signup"),
    path("accounts/find/", account.find_account, name="find_account"),
    path('check-username/', account.check_username, name='check_username'),

    # ---------------------------------------------------------------- [B] 마이페이지
    path("mypage/", mypage.mypage, name="mypage"),
    path("mypage/edit/", mypage.profile_edit, name="profile_edit"),

    # ---------------------------------------------------------------- [C] 댓글
    path("posts/<int:post_id>/comments/", comment.comment_create, name="comment_create"),
    path("comments/<int:comment_id>/delete/", comment.comment_delete, name="comment_delete"),

    # ---------------------------------------------------------------- [C] Q&A
    path("qna/", qna.qna_list, name="qna_list"),
    path("qna/ask/", qna.qna_ask, name="qna_ask"),
    path("qna/<int:post_id>/", qna.qna_detail, name="qna_detail"),
    path("qna/<int:post_id>/answer/", qna.qna_answer, name="qna_answer"),

    # ---------------------------------------------------------------- [C] 쪽지
    path("messages/", message.message_box, name="message_box"),
    path("messages/send/", message.message_send, name="message_send"),
    path("messages/<int:message_id>/", message.message_detail, name="message_detail"),
]
