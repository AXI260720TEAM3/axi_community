from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.urls import reverse  # [추가] reverse 함수 임포트
from ..forms import RecruitApplicationForm, RecruitForm
from ..models import Recruit, RecruitApplication, Notification

# 1. 모집 목록 보기
def recruit_list(request):
    recruits = Recruit.objects.filter(is_deleted=False).select_related('writer')
    
    # 제목/모집분야 검색 필터
    q = request.GET.get('q')
    if q:
        recruits = recruits.filter(title__icontains=q)
        
    return render(request, 'recruit/recruit_list.html', {'recruits': recruits})

# 2. 모집 상세 및 (작성자일 경우) 지원자 목록 보기
def recruit_detail(request, recruit_id):
    recruit = get_object_or_404(Recruit, pk=recruit_id, is_deleted=False)
    applications = recruit.applications.select_related('applicant') if request.user == recruit.writer else None
    
    has_applied = False
    if request.user.is_authenticated:
        has_applied = recruit.applications.filter(applicant=request.user).exists()
        
    return render(request, 'recruit/recruit_detail.html', {
        'recruit': recruit,
        'applications': applications,
        'has_applied': has_applied,
        'is_owner': request.user == recruit.writer,
    })

# 3. 모집글 작성
@login_required
def recruit_create(request):
    if request.method == 'POST':
        form = RecruitForm(request.POST)

        if form.is_valid():
            recruit = form.save(commit=False)
            recruit.writer = request.user
            recruit.save()
            return redirect('recruit_detail', recruit_id=recruit.recruit_id)
    else:
        form = RecruitForm()

    return render(request, 'recruit/recruit_form.html', {'form': form})

# 4. 지원하기 (Notification 알림 연동)
@login_required
def recruit_apply(request, recruit_id):
    recruit = get_object_or_404(Recruit, pk=recruit_id, is_deleted=False)

    if request.user == recruit.writer:
        messages.error(request, "내가 올린 모집에는 지원할 수 없습니다.")
        return redirect('recruit_detail', recruit_id=recruit_id)

    if not recruit.is_recruiting:
        messages.error(request, "이미 마감된 모집입니다.")
        return redirect('recruit_detail', recruit_id=recruit_id)

    if request.method == 'POST':
        form = RecruitApplicationForm(request.POST)

        if not form.is_valid():
            messages.error(request, "지원 메시지를 다시 확인해 주세요.")
            return redirect('recruit_detail', recruit_id=recruit_id)

        app, created = RecruitApplication.objects.get_or_create(
            recruit=recruit,
            applicant=request.user,
            defaults={'message': form.cleaned_data['message']}
        )
        if created:
            # 모집 작성자에게 알림 발송 (link 추가)
            Notification.notify(
                receiver=recruit.writer,
                kind=Notification.Kind.RECRUIT,
                message=f"'{recruit.title}' 모집에 새로운 지원자가 있습니다.",
                link=reverse("recruit_detail", args=[recruit.recruit_id]),  # [수정] 이동할 링크 추가
                actor=request.user
            )
            messages.success(request, "지원서가 제출되었습니다.")
            
    return redirect('recruit_detail', recruit_id=recruit_id)

# 5. 지원 수락/거절/번복 처리 (작성자 전용)
@login_required
@require_POST
def recruit_application_decide(request, app_id, status):
    application = get_object_or_404(RecruitApplication, pk=app_id)
    
    if request.user != application.recruit.writer:
        messages.error(request, "권한이 없습니다.")
        return redirect('recruit_detail', recruit_id=application.recruit.recruit_id)
        
    valid_statuses = {
        RecruitApplication.Status.APPROVED: RecruitApplication.Status.APPROVED,
        RecruitApplication.Status.REJECTED: RecruitApplication.Status.REJECTED,
        RecruitApplication.Status.WAITING: RecruitApplication.Status.WAITING,
    }

    target_status = valid_statuses.get(status)

    if (
        target_status == RecruitApplication.Status.APPROVED
        and application.status != RecruitApplication.Status.APPROVED
        and application.recruit.is_full
    ):
        messages.error(
            request,
            f"모집 인원({application.recruit.headcount}명)을 이미 다 채웠습니다.",
        )
        return redirect('recruit_detail', recruit_id=application.recruit.recruit_id)

    if target_status:
        application.status = target_status
        application.decided_at = timezone.now() if target_status != RecruitApplication.Status.WAITING else None
        application.save()
        
        if target_status == RecruitApplication.Status.APPROVED:
            msg = f"'{application.recruit.title}' 지원 결과: 승인되었습니다."
        elif target_status == RecruitApplication.Status.REJECTED:
            msg = f"'{application.recruit.title}' 지원 결과: 거절되었습니다."
        else:
            msg = f"'{application.recruit.title}' 지원 상태가 '대기'로 재조정되었습니다."

        # 지원자에게 상태 변경 알림 발송 (link 추가)
        Notification.notify(
            receiver=application.applicant,
            kind=Notification.Kind.RECRUIT,
            message=msg,
            link=reverse("recruit_detail", args=[application.recruit.recruit_id]),  # [수정] 이동할 링크 추가
            actor=request.user
        )
        messages.success(request, f"지원 상태가 '{target_status}'(으)로 변경되었습니다.")
        
    return redirect('recruit_detail', recruit_id=application.recruit.recruit_id)

# 6. 모집 조기 마감 처리 (작성자 전용)
@login_required
@require_POST
def recruit_close(request, recruit_id):
    recruit = get_object_or_404(Recruit, pk=recruit_id, writer=request.user)
    recruit.is_closed = True
    recruit.save()
    return redirect('recruit_detail', recruit_id=recruit.recruit_id)

# 7. 팀원 지원 취소 처리 (지원자 전용)
@login_required
def recruit_cancel(request, recruit_id):
    """팀원 지원 취소 처리"""
    if request.method == 'POST':
        recruit = get_object_or_404(Recruit, pk=recruit_id)
        
        application = RecruitApplication.objects.filter(
            recruit=recruit, 
            applicant=request.user
        ).first()

        if application:
            if application.status != '대기':
                messages.error(request, "이미 작성자가 처리를 완료하여 지원을 취소할 수 없습니다.")
            else:
                application.delete()
                messages.success(request, "지원이 성공적으로 취소되었습니다.")
        else:
            messages.error(request, "지원 내역을 찾을 수 없습니다.")

    return redirect('recruit_detail', recruit_id=recruit_id)

# 8. 모집글 삭제 처리 (작성자 전용)
@login_required
def recruit_delete(request, recruit_id):
    recruit = get_object_or_404(Recruit, pk=recruit_id, is_deleted=False)
    
    if request.user != recruit.writer:
        messages.error(request, "삭제 권한이 없습니다.")
        return redirect('recruit_detail', recruit_id=recruit_id)
        
    if request.method == 'POST':
        recruit.is_deleted = True
        recruit.save()
        messages.success(request, "모집글이 삭제되었습니다.")
        return redirect('recruit_list')
        
    return redirect('recruit_detail', recruit_id=recruit_id)