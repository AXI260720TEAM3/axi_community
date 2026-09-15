from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
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
        title = request.POST.get('title')
        content = request.POST.get('content')
        field = request.POST.get('field')
        headcount = request.POST.get('headcount', 1)
        deadline = request.POST.get('deadline')

        recruit = Recruit.objects.create(
            writer=request.user,
            title=title,
            content=content,
            field=field,
            headcount=headcount,
            deadline=deadline,
        )
        return redirect('recruit_detail', recruit_id=recruit.recruit_id)
        
    return render(request, 'recruit/recruit_form.html')

# 4. 지원하기 (Notification 알림 연동)
@login_required
def recruit_apply(request, recruit_id):
    recruit = get_object_or_404(Recruit, pk=recruit_id, is_deleted=False)
    
    if recruit.is_closed or recruit.deadline < timezone.now().date():
        messages.error(request, "이미 마감된 모집입니다.")
        return redirect('recruit_detail', recruit_id=recruit_id)
        
    if request.method == 'POST':
        message_text = request.POST.get('message', '')
        app, created = RecruitApplication.objects.get_or_create(
            recruit=recruit,
            applicant=request.user,
            defaults={'message': message_text}
        )
        if created:
            # 모집 작성자에게 알림 발송
            Notification.notify(
                receiver=recruit.writer,
                kind=Notification.Kind.RECRUIT,
                message=f"'{recruit.title}' 모집에 새로운 지원자가 있습니다.",
                actor=request.user
            )
            messages.success(request, "지원서가 제출되었습니다.")
            
    return redirect('recruit_detail', recruit_id=recruit_id)

# 5. 지원 수락/거절 처리 (작성자 전용)
@login_required
def recruit_application_decide(request, app_id, status):
    application = get_object_or_404(RecruitApplication, pk=app_id)
    
    if request.user != application.recruit.writer:
        messages.error(request, "권한이 없습니다.")
        return redirect('recruit_detail', recruit_id=application.recruit.recruit_id)
        
    if status in [RecruitApplication.Status.APPROVED, RecruitApplication.Status.REJECTED]:
        application.status = status
        application.decided_at = timezone.now()
        application.save()
        
        # 지원자에게 수락/거절 결과 알림 발송
        Notification.notify(
            receiver=application.applicant,
            kind=Notification.Kind.RECRUIT,
            message=f"'{application.recruit.title}' 지원 결과: {status} 되었습니다.",
            actor=request.user
        )
        
    return redirect('recruit_detail', recruit_id=application.recruit.recruit_id)

# 6. 모집 조기 마감 처리 (작성자 전용)
@login_required
def recruit_close(request, recruit_id):
    recruit = get_object_or_404(Recruit, pk=recruit_id, writer=request.user)
    recruit.is_closed = True
    recruit.save()
    return redirect('recruit_detail', recruit_id=recruit.recruit_id)

@login_required
def recruit_cancel(request, recruit_id):
    """팀원 지원 취소 처리"""
    if request.method == 'POST':
        recruit = get_object_or_404(Recruit, pk=recruit_id)
        
        # 본인의 지원 내역 조회
        application = RecruitApplication.objects.filter(
            recruit=recruit, 
            applicant=request.user
        ).first()

        if application:
            # 이미 승인/거절 처리된 지원건은 취소할 수 없도록 방어
            if application.status != '대기':
                messages.error(request, "이미 작성자가 처리를 완료하여 지원을 취소할 수 없습니다.")
            else:
                application.delete()
                messages.success(request, "지원이 성공적으로 취소되었습니다.")
        else:
            messages.error(request, "지원 내역을 찾을 수 없습니다.")

    return redirect('recruit_detail', recruit_id=recruit_id)

@login_required
def recruit_cancel(request, recruit_id):
    """팀원 지원 취소 처리"""
    if request.method == 'POST':
        recruit = get_object_or_404(Recruit, pk=recruit_id)
        
        # 본인의 지원 내역 조회
        application = RecruitApplication.objects.filter(
            recruit=recruit, 
            applicant=request.user
        ).first()

        if application:
            # 이미 승인/거절 처리된 지원건은 취소할 수 없도록 방어
            if application.status != '대기':
                messages.error(request, "이미 작성자가 처리를 완료하여 지원을 취소할 수 없습니다.")
            else:
                application.delete()
                messages.success(request, "지원이 성공적으로 취소되었습니다.")
        else:
            messages.error(request, "지원 내역을 찾을 수 없습니다.")

    return redirect('recruit_detail', recruit_id=recruit_id)