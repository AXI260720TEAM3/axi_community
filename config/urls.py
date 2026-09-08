"""
프로젝트 전체 URL — 팀장이 관리합니다.

화면 URL 은 community/urls.py 에 모아두었습니다. 여기는 건드릴 일이 거의 없습니다.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('community.urls')),
]

# 개발 중에만 업로드된 첨부파일을 Django 가 직접 내려줍니다.
# 배포할 때는 웹서버가 대신 처리하므로 이 줄은 동작하지 않습니다.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
