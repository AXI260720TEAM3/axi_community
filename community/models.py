"""
국비학원 정보공유 커뮤니티 게시판 — 데이터 모델

ERD 대응
    user_type        -> UserType
    member           -> Member          (AbstractUser 상속)
    board            -> Board
    board_permission -> BoardPermission (M:N 중간 모델)
    post             -> Post            (Q&A 답변은 parent 자기참조)
    post_comment     -> PostComment
    attachment       -> Attachment
    message          -> Message

테이블명과 컬럼명은 ERD(국비학원커뮤니티_테스트DB.sql)와 똑같이 맞췄습니다.
그래야 스크립트의 샘플 데이터 INSERT 를 그대로 넣을 수 있습니다.
Django 가 붙이는 이름과 다른 곳에는 db_column 을 지정했습니다.

    login_id        <- username        (AbstractUser 상속 필드를 다시 선언)
    joined_at       <- date_joined     (같음)
    type_id         <- user_type_id    (Member, BoardPermission)
    parent_post_id  <- parent_id       (Post)

settings.py 에 아래 한 줄이 반드시 필요합니다.
    AUTH_USER_MODEL = "community.Member"

이 설정은 첫 makemigrations 전에 넣어야 합니다.
나중에 바꾸면 데이터베이스를 통째로 지우고 다시 만들어야 합니다.
"""

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


# ================================================================ 회원

class UserType(models.Model):
    """수강생 / 강사 / 멘토 / 직원"""

    type_id = models.AutoField(primary_key=True)
    type_name = models.CharField("유형명", max_length=50, unique=True)

    class Meta:
        db_table = "user_type"
        verbose_name = "회원 유형"
        verbose_name_plural = "회원 유형"

    def __str__(self):
        return self.type_name


class MemberManager(UserManager):
    """
    Member 는 member_name, phone, address, user_type 이 필수라서
    기본 UserManager 로는 createsuperuser 가 실패합니다.
    관리자 계정은 '직원' 유형으로 만들고 나머지는 기본값으로 채웁니다.

    주의: 샘플 데이터를 먼저 넣고 createsuperuser 를 나중에 실행하세요.
    순서를 바꾸면 get_or_create 가 '직원'을 type_id=1 로 만들어버려서
    샘플 데이터의 (1, '수강생') 과 기본키가 충돌합니다.
    """

    def create_superuser(self, username, email=None, password=None, **extra):
        staff_type, _ = UserType.objects.get_or_create(type_name="직원")
        extra.setdefault("member_name", username)
        extra.setdefault("phone", "01000000000")
        extra.setdefault("address", "-")
        extra.setdefault("user_type", staff_type)
        return super().create_superuser(username, email, password, **extra)


class Member(AbstractUser):
    """
    회원.

    AbstractUser 가 이미 갖고 있어 다시 선언하지 않은 필드
        password    -> 해시로 저장됨. 8자 이상·영문+숫자 검증은 폼에서
        last_login  -> 마지막 로그인 시각
        is_active / is_staff / is_superuser -> 인증과 관리자 화면에 필요

    username 과 date_joined 는 컬럼명을 ERD 에 맞추려고 다시 선언했습니다.
    추상 클래스에서 상속받은 필드는 이렇게 덮어쓸 수 있습니다.

    쓰지 않는 상속 필드는 아래에서 비웁니다.
    """

    first_name = None
    last_name = None

    # ---- 상속 필드 재선언 (컬럼명을 ERD 에 맞춘다)
    username = models.CharField(
        "아이디",
        max_length=50,
        unique=True,
        db_column="login_id",
        validators=[UnicodeUsernameValidator()],
        error_messages={"unique": "이미 사용 중인 아이디입니다."},
    )
    date_joined = models.DateTimeField(
        "가입일시",
        default=timezone.now,
        db_column="joined_at",
    )

    # ---- 고유 필드
    member_id = models.AutoField(primary_key=True)
    member_name = models.CharField("이름", max_length=50)
    email = models.EmailField("이메일", max_length=100)
    phone = models.CharField(
        "전화번호",
        max_length=11,
        validators=[RegexValidator(r"^\d{10,11}$", "숫자만 10자리 또는 11자리로 입력하세요.")],
    )
    address = models.CharField("주소", max_length=200)
    user_type = models.ForeignKey(
        UserType,
        on_delete=models.PROTECT,          # ON DELETE RESTRICT
        db_column="type_id",
        related_name="members",
        verbose_name="회원 유형",
    )

    objects = MemberManager()

    # createsuperuser 가 추가로 물어볼 항목. 나머지는 MemberManager 가 채웁니다.
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "member"
        verbose_name = "회원"
        verbose_name_plural = "회원"

    def __str__(self):
        return f"{self.member_name}({self.username})"


# ================================================================ 게시판

class Board(models.Model):
    """공지사항 / 자유게시판 / Q&A / 취업정보"""

    board_id = models.AutoField(primary_key=True)
    board_name = models.CharField("게시판명", max_length=50, unique=True)
    allow_comment = models.BooleanField("댓글 허용", default=True)

    class Meta:
        db_table = "board"
        verbose_name = "게시판"
        verbose_name_plural = "게시판"

    def __str__(self):
        return self.board_name


class BoardPermission(models.Model):
    """
    게시판 × 회원유형 작성 권한.

    여기 있는 조합만 허용됩니다. 없는 조합은 자동으로 금지입니다.
    게시판이나 회원유형이 늘어나도 코드를 고칠 필요가 없습니다.

    ERD 에서는 (board_id, type_id, permission_type) 복합 기본키였습니다.
    Django 는 복합 기본키를 지원하지 않으므로 대리키 + UniqueConstraint 로 옮겼습니다.
    저장값은 ERD 와 같은 한글('일반'/'질문'/'답변')을 씁니다.
    """

    class PermissionType(models.TextChoices):
        GENERAL = "일반", "일반"
        QUESTION = "질문", "질문"
        ANSWER = "답변", "답변"

    board = models.ForeignKey(
        Board, on_delete=models.CASCADE, related_name="permissions", verbose_name="게시판"
    )
    user_type = models.ForeignKey(
        UserType,
        on_delete=models.CASCADE,
        db_column="type_id",
        related_name="permissions",
        verbose_name="회원 유형",
    )
    permission_type = models.CharField(
        "권한 구분",
        max_length=10,
        choices=PermissionType.choices,
        default=PermissionType.GENERAL,
    )

    class Meta:
        db_table = "board_permission"
        verbose_name = "작성 권한"
        verbose_name_plural = "작성 권한"
        constraints = [
            models.UniqueConstraint(
                fields=["board", "user_type", "permission_type"],
                name="uq_board_permission",
            )
        ]

    def __str__(self):
        return f"{self.board} · {self.user_type} · {self.get_permission_type_display()}"


# ================================================================ 게시글

class PostQuerySet(models.QuerySet):
    def visible(self):
        """삭제 플래그가 서지 않은 글만"""
        return self.filter(is_deleted=False)

    def roots(self):
        """원글만. Q&A 답변은 parent 가 있으므로 제외"""
        return self.filter(parent__isnull=True)


class Post(models.Model):
    """
    게시글.

    Q&A 답변도 게시글로 저장하고 parent 로 원 질문을 가리킵니다.
    다른 게시판의 글은 parent 가 항상 비어 있습니다.
    """

    post_id = models.AutoField(primary_key=True)
    board = models.ForeignKey(
        Board, on_delete=models.PROTECT, related_name="posts", verbose_name="게시판"
    )
    writer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="posts",
        verbose_name="작성자",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_column="parent_post_id",
        related_name="answers",
        verbose_name="원 질문",
    )
    title = models.CharField("제목", max_length=250)
    content = models.TextField("내용")
    created_at = models.DateTimeField("작성일시", auto_now_add=True)
    updated_at = models.DateTimeField("수정일시", null=True, blank=True)
    is_deleted = models.BooleanField("삭제 여부", default=False)

    objects = PostQuerySet.as_manager()

    class Meta:
        db_table = "post"
        verbose_name = "게시글"
        verbose_name_plural = "게시글"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["board", "-created_at"], name="ix_post_board_created"),
            models.Index(fields=["parent"], name="ix_post_parent"),
        ]

    def __str__(self):
        return self.title

    @property
    def is_answer(self):
        """이 글이 Q&A 답변인지"""
        return self.parent_id is not None


class PostComment(models.Model):
    """댓글. Q&A 게시판(allow_comment=False)에는 달 수 없습니다."""

    comment_id = models.AutoField(primary_key=True)
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments", verbose_name="게시글"
    )
    writer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="comments",
        verbose_name="작성자",
    )
    content = models.TextField("내용")
    created_at = models.DateTimeField("작성일시", auto_now_add=True)
    is_deleted = models.BooleanField("삭제 여부", default=False)

    class Meta:
        db_table = "post_comment"
        verbose_name = "댓글"
        verbose_name_plural = "댓글"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.post} 의 댓글"


class Attachment(models.Model):
    """게시글 첨부파일. 한 게시글에 여러 개 올릴 수 있습니다."""

    attachment_id = models.AutoField(primary_key=True)
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="attachments", verbose_name="게시글"
    )
    origin_name = models.CharField("원본 파일명", max_length=255)
    stored_path = models.FileField("저장 경로", upload_to="attachments/%Y/%m/", max_length=500)
    file_size = models.BigIntegerField("파일 크기")
    uploaded_at = models.DateTimeField("업로드일시", auto_now_add=True)

    class Meta:
        db_table = "attachment"
        verbose_name = "첨부파일"
        verbose_name_plural = "첨부파일"
        ordering = ["attachment_id"]

    def __str__(self):
        return self.origin_name


# ================================================================ 쪽지

class Message(models.Model):
    """회원 사이의 1:1 쪽지. read_at 이 비어 있으면 아직 읽지 않은 쪽지입니다."""

    message_id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_messages",
        verbose_name="보낸 사람",
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_messages",
        verbose_name="받는 사람",
    )
    content = models.TextField("내용")
    sent_at = models.DateTimeField("발송일시", auto_now_add=True)
    read_at = models.DateTimeField("읽음일시", null=True, blank=True)

    class Meta:
        db_table = "message"
        verbose_name = "쪽지"
        verbose_name_plural = "쪽지"
        ordering = ["-sent_at"]
        indexes = [
            models.Index(fields=["receiver", "-sent_at"], name="ix_message_receiver"),
        ]

    def __str__(self):
        return f"{self.sender} → {self.receiver}"

    @property
    def is_read(self):
        return self.read_at is not None
