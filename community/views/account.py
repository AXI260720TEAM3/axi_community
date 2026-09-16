import logging
import secrets
import string

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.http import JsonResponse
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme

from community.forms import SignupForm

User = get_user_model()

logger = logging.getLogger(__name__)

# 임시 비밀번호를 다시 발급받을 수 있을 때까지의 대기 시간(초)
RESET_COOLDOWN = 180


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


def check_username(request):
    """아이디 중복 확인 AJAX API"""
    username = request.GET.get('username', '').strip()
    is_taken = User.objects.filter(username=username).exists()
    return JsonResponse({'is_taken': is_taken})


def login_view(request):
    """로그인 처리"""
    # @login_required 가 보낸 주소. 로그인 뒤 원래 보려던 화면으로 되돌려 보냅니다.
    next_url = request.POST.get('next') or request.GET.get('next') or ''

    if request.method == 'POST':
        username_val = request.POST.get('username')
        password_val = request.POST.get('password')

        user = authenticate(request, username=username_val, password=password_val)
        if user is not None:
            login(request, user)

            # 주소를 그대로 믿으면 다른 사이트로 튕겨 보낼 수 있습니다(오픈 리다이렉트).
            # 우리 호스트로 가는 주소일 때만 씁니다.
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

            return redirect('home')
        else:
            messages.error(request, "아이디 또는 비밀번호가 올바르지 않습니다.")

    return render(request, 'account/login.html', {'next': next_url})


def logout_view(request):
    """로그아웃 처리"""
    logout(request)
    return redirect('home')


def find_account(request):
    """아이디 및 비밀번호 찾기 (임시 비밀번호 이메일 발송)"""
    found_id = None
    
    if request.method == 'POST':
        mode = request.POST.get('mode')
        
        # 1. 아이디 찾기
        if mode == 'find_id':
            name = request.POST.get('member_name')
            email = request.POST.get('email')

            # 이메일에는 unique 제약이 없습니다. 이름과 이메일이 같은 계정이 둘 이상이면
            # get() 은 MultipleObjectsReturned 로 500 을 냅니다. filter() 로 모두 받습니다.
            users = User.objects.filter(member_name=name, email=email).order_by('member_id')

            masked_ids = []
            for user in users:
                raw_id = user.username
                if len(raw_id) > 4:
                    masked_ids.append(raw_id[:3] + '***' + raw_id[-2:])
                else:
                    masked_ids.append(raw_id[:1] + '***')

            if masked_ids:
                found_id = ', '.join(masked_ids)
            else:
                messages.error(request, "일치하는 회원 정보를 찾을 수 없습니다.")

        # 2. 비밀번호 찾기 (임시 비밀번호 발송)
        elif mode == 'find_pw':
            username = (request.POST.get('username') or '').strip()
            email = (request.POST.get('email') or '').strip()

            # 아이디와 이메일만 알면 남의 비밀번호를 몇 번이고 초기화시킬 수 있습니다.
            # 같은 계정에 대한 재발급은 RESET_COOLDOWN 초 동안 막습니다.
            throttle_key = f'pw_reset:{username.lower()}'

            if username and cache.get(throttle_key):
                messages.error(request, "임시 비밀번호는 잠시 후에 다시 요청할 수 있습니다.")
                return render(request, 'account/find.html', {'found_id': found_id})

            try:
                user = User.objects.get(username=username, email=email)
            except User.DoesNotExist:
                messages.error(request, "입력하신 아이디와 이메일 정보가 일치하는 회원이 없습니다.")
            else:
                # 8자리 무작위 임시 비밀번호 생성 (영문+숫자)
                chars = string.ascii_letters + string.digits
                temp_password = ''.join(secrets.choice(chars) for _ in range(8))

                # 이메일 전송 내용 작성
                subject = '[기회를 IT-DA] 임시 비밀번호가 발급되었습니다.'
                message = (
                    f"안녕하세요 {user.member_name}님,\n\n"
                    f"요청하신 임시 비밀번호는 다음과 같습니다.\n\n"
                    f"임시 비밀번호: {temp_password}\n\n"
                    f"로그인 후 마이페이지에서 반드시 비밀번호를 변경해 주세요."
                )

                try:
                    # 메일을 먼저 보냅니다. 비밀번호부터 바꾸면 발송이 실패했을 때
                    # 임시 비밀번호를 받지 못한 채 기존 비밀번호만 사라져 계정이 잠깁니다.
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                except Exception:
                    logger.exception("임시 비밀번호 메일 발송 실패: username=%s", username)
                    messages.error(request, "이메일 발송 중 오류가 발생했습니다. 비밀번호는 그대로입니다. 잠시 후 다시 시도해 주세요.")
                else:
                    # 발송에 성공했을 때만 비밀번호를 바꿉니다.
                    user.set_password(temp_password)
                    user.save(update_fields=['password'])

                    cache.set(throttle_key, True, RESET_COOLDOWN)
                    messages.success(request, f"{user.email} 주소로 임시 비밀번호를 발송했습니다.")

    return render(request, 'account/find.html', {'found_id': found_id})