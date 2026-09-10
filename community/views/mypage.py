from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required

from community.models import Post, Board


@login_required
def mypage(request):
    user = request.user

    # 내가 쓴 글 목록
    my_posts = Post.objects.visible().filter(writer=user).order_by('-created_at')

    # 게시판 이름(board_name)으로 직접 카운트 조회
    free_post_count = my_posts.filter(board__board_name='자유게시판').count()
    qna_count = my_posts.filter(board__board_name='Q&A').count()

    context = {
        'nav_current': 'mypage',
        'my_posts': my_posts,
        'free_post_count': free_post_count,
        'qna_count': qna_count,
        'comment_count': 0,
        'unread_message_count': 0,
    }

    return render(request, "mypage/index.html", context)


@login_required
def profile_edit(request):
    """회원정보 수정 및 비밀번호 변경"""
    if request.method == 'POST':
        user = request.user

        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        new_password = request.POST.get('new_password')
        new_password_confirm = request.POST.get('new_password_confirm')

        # 1. 기본 회원정보 업데이트 (이메일, 전화번호, 주소)
        if email:
            user.email = email
        if phone is not None:
            user.phone = phone
        if address is not None:
            user.address = address

        # 2. 비밀번호 변경 로직
        if new_password:
            # 비밀번호 확인 일치 검증
            if new_password != new_password_confirm:
                messages.error(request, "새 비밀번호가 서로 일치하지 않습니다.")
                return redirect('mypage')
            
            # 최소 자릿수 검증
            if len(new_password) < 8:
                messages.error(request, "비밀번호는 최소 8자 이상이어야 합니다.")
                return redirect('mypage')

            # set_password로 비밀번호 해시화 저장
            user.set_password(new_password)
            user.save()

            # 비밀번호 변경 후 로그아웃 방지 (세션 갱신)
            update_session_auth_hash(request, user)
            messages.success(request, "비밀번호 및 회원정보가 변경되었습니다.")
            return redirect('mypage')

        # 비밀번호를 변경하지 않고 기본 정보만 수정하는 경우
        user.save()
        messages.success(request, "회원정보가 수정되었습니다.")
        return redirect('mypage')

    return render(request, "mypage/index.html", {"nav_current": "mypage"})


@login_required
def my_posts_ajax(request):
  """내가 쓴 글 탭 클릭 시 AJAX 요청을 처리하는 뷰"""
  board_name = request.GET.get('board_name', '자유게시판')

  # 1. 로그인한 사용자(request.user)가 쓴 글 중
  # 2. 선택한 게시판 이름과 일치하고
  # 3. 삭제되지 않은(is_deleted=False) 글만 조회
  posts = (
      Post.objects.filter(
          writer=request.user, board__board_name=board_name, is_deleted=False
      )
      .select_related('board')
      .order_by('-created_at')
  )

  context = {'posts': posts}

  # 아래 2번에서 만들 조각 템플릿으로 렌더링
  return render(request, 'account/partials/my_post_list.html', context)