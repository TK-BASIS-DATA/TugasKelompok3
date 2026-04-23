from django import forms
from django.contrib.auth import authenticate

from .models import MASKAPAI_CHOICES, User


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "Email"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password"}))

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        if email and password:
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("Email atau password salah.")
            if not self.user_cache.is_active:
                raise forms.ValidationError("Akun tidak aktif.")
        return cleaned_data

    def get_user(self):
        return self.user_cache


class BaseRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = [
            "email",
            "salutation",
            "first_mid_name",
            "last_name",
            "country_code",
            "mobile_number",
            "tanggal_lahir",
            "kewarganegaraan",
        ]
        widgets = {
            "tanggal_lahir": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email sudah terdaftar.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("confirm_password"):
            raise forms.ValidationError("Password dan konfirmasi password harus sama.")
        return cleaned_data


class MemberRegistrationForm(BaseRegistrationForm):
    pass


class StaffRegistrationForm(BaseRegistrationForm):
    kode_maskapai = forms.ChoiceField(choices=MASKAPAI_CHOICES)
