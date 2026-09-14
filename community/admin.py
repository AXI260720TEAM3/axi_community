from django.contrib import admin
from .models import (
    UserType, Board, BoardPermission, Member,
    Post, PostComment, Attachment, Message,
    Bookmark, PostLike, Notification, Recruit, RecruitApplication,
)

admin.site.register([
    UserType, Board, BoardPermission, Member,
    Post, PostComment, Attachment, Message,
    Bookmark, PostLike, Notification, Recruit, RecruitApplication,
])

# Register your models here.
