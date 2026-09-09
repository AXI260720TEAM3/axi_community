from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from community.forms import SignupForm

def signup(request):
    """회원가입 처리"""
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "회원가입이 완료되었습니다. 로그인해 주세요.")
            return redirect('login')
        else:
            messages.error(request, "입력한 정보를 다시 확인해 주세요.")
    else:
        form = SignupForm()
    
    return render(request, 'account/signup.html', {'form': form})


def login_view(request):
    """로그인 처리"""
    if request.method == 'POST':
        username_val = request.POST.get('username')
        password_val = request.POST.get('password')
        
        user = authenticate(request, username=username_val, password=password_val)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "아이디 또는 비밀번호가 올바르지 않습니다.")
            
    # 템플릿 경로를 'account/login.html'로 수정
    return render(request, 'account/login.html')


def logout_view(request):
    """로그아웃 처리"""
    logout(request)
    return redirect('login')

User = get_user_model()

def find_account(request):
    found_id = None
    
    if request.method == 'POST':
        mode = request.POST.get('mode')
        
        # 1. 아이디 찾기 처리
        if mode == 'find_id':
            name = request.POST.get('member_name')
            email = request.POST.get('email')
            try:
                user = User.objects.get(member_name=name, email=email)
                # 아이디 일부 마스킹 처리 (예: mentee_kim -> men***kim)
                raw_id = user.username
                if len(raw_id) > 4:
                    found_id = raw_id[:3] + '***' + raw_id[-2:]
                else:
                    found_id = raw_id[:1] + '***'
            except User.DoesNotExist:
                messages.error(request, "일치하는 회원 정보를 찾을 수 없습니다.")

        # 2. 비밀번호 찾기 처리
        elif mode == 'find_pw':
            username = request.POST.get('username')
            email = request.POST.get('email')
            if User.objects.filter(username=username, email=email).exists():
                messages.success(request, "비밀번호 재설정 안내를 전달했습니다.")
            else:
                messages.error(request, "입력하신 아이디와 이메일 정보가 일치하지 않습니다.")

    return render(request, 'account/find.html', {'found_id': found_id})

import secrets
import string
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()

def find_account(request):
    found_id = None
    
    if request.method == 'POST':
        mode = request.POST.get('mode')
        
        # 1. 아이디 찾기
        if mode == 'find_id':
            name = request.POST.get('member_name')
            email = request.POST.get('email')
            try:
                user = User.objects.get(member_name=name, email=email)
                raw_id = user.username
                if len(raw_id) > 4:
                    found_id = raw_id[:3] + '***' + raw_id[-2:]
                else:
                    found_id = raw_id[:1] + '***'
            except User.DoesNotExist:
                messages.error(request, "일치하는 회원 정보를 찾을 수 없습니다.")

        # 2. 비밀번호 찾기 (임시 비밀번호 발송)
        elif mode == 'find_pw':
            username = request.POST.get('username')
            email = request.POST.get('email')
            
            try:
                user = User.objects.get(username=username, email=email)
                
                # 8자리 무작위 임시 비밀번호 생성 (영문+숫자)
                chars = string.ascii_letters + string.digits
                temp_password = ''.join(secrets.choice(chars) for _ in range(8))
                
                # 회원 비밀번호 변경 및 저장 (해싱 적용)
                user.set_password(temp_password)
                user.save()
                
                # 이메일 전송 내용 작성
                subject = '[모두의국비] 임시 비밀번호가 발급되었습니다.'
                message = (
                    f"안녕하세요 {user.member_name}님,\n\n"
                    f"요청하신 임시 비밀번호는 다음과 같습니다.\n\n"
                    f"임시 비밀번호: {temp_password}\n\n"
                    f"로그인 후 마이페이지에서 반드시 비밀번호를 변경해 주세요."
                )
                
                # 실제 메일 발송
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                messages.success(request, f"{email} 주소로 임시 비밀번호를 발송했습니다.")
                
            except User.DoesNotExist:
                messages.error(request, "입력하신 아이디와 이메일 정보가 일치하는 회원이 없습니다.")
            except Exception as e:
                messages.error(request, "이메일 발송 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")

    return render(request, 'account/find.html', {'found_id': found_id})

