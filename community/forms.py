from django import forms
from django.contrib.auth import get_user_model
from community.models import UserType

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