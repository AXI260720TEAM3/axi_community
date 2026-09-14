"""
프로젝트 전체 URL — 팀장이 관리합니다.

화면 URL 은 community/urls.py 에 모아두었습니다. 여기는 건드릴 일이 거의 없습니다.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('community.urls')),
]

# 업로드된 첨부파일은 /media/ 주소로 직접 내려주지 않습니다.
# 그렇게 하면 로그인하지 않아도 받아지고, .html 파일을 올렸을 때
# 우리 사이트 안에서 그대로 열려 스크립트가 실행될 수 있습니다.
# 다운로드는 attachment_download 뷰(권한 확인 + 항상 저장)만 통과합니다.
