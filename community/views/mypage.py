from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from community.forms import ProfileEditForm
from community.models import Post, Board, Message, PostLike


@login_required
def mypage(request):
    user = request.user

    # 내가 쓴 글 목록
    my_posts = Post.objects.visible().filter(writer=user).order_by('-created_at')

    # 게시판 이름(board_name)으로 직접 카운트 조회
    free_post_count = my_posts.filter(board__board_name='자유게시판').count()
    qna_count = my_posts.filter(board__board_name='Q&A').count()

    # 안 읽은 쪽지 수. 사이드바 배지와 같은 기준을 씁니다
    unread_count = Message.objects.unread_for(user).count()

    context = {
        'nav_current': 'mypage',
        'my_posts': my_posts,
        'free_post_count': free_post_count,
        'qna_count': qna_count,
        'comment_count': 0,
        'unread_message_count': unread_count,
    }

    return render(request, "mypage/index.html", context)


@login_required
def profile_edit(request):
    """회원정보 수정 및 비밀번호 변경"""
    if request.method == 'POST':
        user = request.user

        current_password = request.POST.get('current_password')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        new_password = request.POST.get('new_password')
        new_password_confirm = request.POST.get('new_password_confirm')

        # 0. 필수: 현재 비밀번호 검증
        if not current_password or not user.check_password(current_password):
            messages.error(request, "현재 비밀번호가 일치하지 않습니다.")
            return redirect('mypage')

        # 1. 기본 회원정보 검증 (이메일 형식, 전화번호 숫자 10~11자리, 길이 제한)
        #    user.save() 만 부르면 모델에 걸어둔 검사가 하나도 실행되지 않습니다.
        form = ProfileEditForm(
            {'email': email, 'phone': phone, 'address': address},
            instance=user,
        )

        if not form.is_valid():
            for field_errors in form.errors.values():
                for text in field_errors:
                    messages.error(request, text)
            return redirect('mypage')

        # 2. 비밀번호 변경 로직
        if new_password:
            # 비밀번호 확인 일치 검증
            if new_password != new_password_confirm:
                messages.error(request, "새 비밀번호가 서로 일치하지 않습니다.")
                return redirect('mypage')

            # settings.AUTH_PASSWORD_VALIDATORS 를 그대로 적용합니다.
            # 길이만 보면 '12345678' 같은 비밀번호가 그대로 통과합니다.
            try:
                validate_password(new_password, user)
            except ValidationError as exc:
                for text in exc.messages:
                    messages.error(request, text)
                return redirect('mypage')

            user = form.save(commit=False)

            # set_password로 비밀번호 해시화 저장
            user.set_password(new_password)
            user.save()

            # 비밀번호 변경 후 로그아웃 방지 (세션 갱신)
            update_session_auth_hash(request, user)
            messages.success(request, "비밀번호 및 회원정보가 변경되었습니다.")
            return redirect('mypage')

        # 비밀번호를 변경하지 않고 기본 정보만 수정하는 경우
        form.save()
        messages.success(request, "회원정보가 수정되었습니다.")
        return redirect('mypage')

    return render(request, "mypage/index.html", {"nav_current": "mypage"})


@login_required
def my_posts_ajax(request):
    """내가 쓴 글 및 추천한 글 탭 클릭 시 AJAX 요청을 처리하는 뷰"""
    board_name = request.GET.get('board_name', '자유게시판')
    user = request.user

    # 1. '추천한글' 탭 클릭 시
    if board_name == '추천한글':
        # PostLike 테이블을 통해 내가 좋아요를 누른 게시글 목록 조회
        posts = (
            Post.objects.filter(
                likes__member=user,  
                is_deleted=False
            )
            .select_related('board', 'writer')
            .order_by('-likes__created_at')  # 추천 누른 최근 순 정렬
        )
        
        # 만약 ManyToManyField (예: likes = models.ManyToManyField(User)) 관계라면:
        # posts = Post.objects.filter(likes=user, is_deleted=False).select_related('board', 'writer').order_by('-created_at')

    # 2. 일반 게시판 탭 클릭 시 (내가 쓴 글)
    else:
        posts = (
            Post.objects.filter(
                writer=user, 
                board__board_name=board_name, 
                is_deleted=False
            )
            .select_related('board')
            .order_by('-created_at')
        )

    context = {'posts': posts, 'board_name': board_name}
    return render(request, 'account/partials/my_post_list.html', context)

@login_required
def account_delete(request):
    """회원 탈퇴 처리 (소프트 삭제)"""
    if request.method == 'POST':
        user = request.user
        
        # 계정 비활성화 처리
        user.is_active = False
        user.save()
        
        # 로그아웃
        logout(request)
        
        messages.success(request, "회원 탈퇴가 완료되었습니다. 그동안 이용해 주셔서 감사합니다.")
        return redirect('home')

    return redirect('mypage')
