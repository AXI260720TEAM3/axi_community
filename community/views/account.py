"""
[B] 회원가입 · 로그인 · 로그아웃 · 계정찾기

Django 의 django.contrib.auth 가 대부분을 제공합니다. 직접 만들지 마세요.
    authenticate(request, username=..., password=...)   비밀번호 대조
    login(request, user)  /  logout(request)            세션 처리
비밀번호는 반드시 set_password() 로 저장합니다. 평문으로 넣으면 로그인이 안 됩니다.

로그인 아이디는 ERD 의 login_id 이고, 모델에서는 username 필드입니다.
(컬럼명만 login_id 로 맞춰두었습니다)
"""

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render


def login_view(request):
    # TODO [B] POST 면 authenticate → login → redirect('home')
    #          실패하면 messages.error 로 안내하고 다시 로그인 화면
    return render(request, "account/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


def signup(request):
    # TODO [B] forms.py 에 SignupForm 을 만들어 검증
    #          아이디 중복, 비밀번호 확인, 전화번호 형식, 회원유형 선택
    #          Member.objects.create_user(...) 를 쓰면 비밀번호가 자동으로 해시됩니다
    return render(request, "account/signup.html")


def find_account(request):
    # TODO [B] 이름 + 이메일로 아이디 찾기 / 아이디 + 이메일로 비밀번호 재설정
    return render(request, "account/find.html")
