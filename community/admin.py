from django.contrib import admin
from .models import (
    UserType, Board, BoardPermission, Member,
    Post, PostComment, Attachment, Message,
)

admin.site.register([
    UserType, Board, BoardPermission, Member,
    Post, PostComment, Attachment, Message,
])

# Register your models here.
