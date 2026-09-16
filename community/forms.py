from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from community.models import UserType
from .models import Recruit, RecruitApplication

User = get_user_model()

class SignupForm(forms.ModelForm):
    password = forms.CharField(
        label="비밀번호",
        widget=forms.PasswordInput,
        min_length=8,
        error_messages={'min_length': '비밀번호는 8자 이상이어야 합니다.'}
    )
    password_confirm = forms.CharField(
        label="비밀번호 확인",
        widget=forms.PasswordInput
    )
    # write_only=True 제거 및 required=False 적용
    user_type_name = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ['username', 'password', 'member_name', 'phone', 'email', 'address']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "비밀번호가 일치하지 않습니다.")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        type_name = self.cleaned_data.get("user_type_name") or "수강생"
        try:
            user_type_obj = UserType.objects.get(type_name=type_name)
        except UserType.DoesNotExist:
            user_type_obj = UserType.objects.get(type_name="수강생")
        
        user.user_type = user_type_obj

        if commit:
            user.save()
        return user

class RecruitForm(forms.ModelForm):
    """모집글 작성 폼.

    브라우저의 required 는 개발자 도구나 curl 로 쉽게 지나칠 수 있습니다.
    빈 값·과거 날짜·이상한 인원수는 여기서 걸러야 뷰가 500 으로 죽지 않습니다.
    """

    class Meta:
        model = Recruit
        fields = ['title', 'field', 'headcount', 'deadline', 'content']
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
        }
        error_messages = {
            'title': {'required': '모집 제목을 입력하세요.'},
            'field': {'required': '모집 분야를 입력하세요.'},
            'content': {'required': '프로젝트 소개를 입력하세요.'},
            'headcount': {'required': '모집 인원을 입력하세요.',
                          'invalid': '모집 인원은 숫자로 입력하세요.'},
            'deadline': {'required': '모집 마감일을 입력하세요.',
                         'invalid': '모집 마감일을 날짜로 입력하세요.'},
        }

    def clean_headcount(self):
        headcount = self.cleaned_data['headcount']

        if headcount < 1:
            raise forms.ValidationError("모집 인원은 1명 이상이어야 합니다.")

        return headcount

    def clean_deadline(self):
        deadline = self.cleaned_data['deadline']

        # 지난 날짜로 올리면 목록에 뜨자마자 마감된 글이 됩니다.
        if deadline < timezone.now().date():
            raise forms.ValidationError("마감일은 오늘 이후로 정해주세요.")

        return deadline


class RecruitApplicationForm(forms.ModelForm):
    class Meta:
        model = RecruitApplication
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': '간단한 자기소개나 지원 동기를 남겨주세요.'}),
        }