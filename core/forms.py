from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm

from .models import MASKAPAI_CHOICES, StaffProfile, User


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



class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
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


class StaffMaskapaiForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = ["kode_maskapai"]


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(label="Password Lama", widget=forms.PasswordInput)
    new_password1 = forms.CharField(label="Password Baru", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Konfirmasi Password Baru", widget=forms.PasswordInput)


class ClaimMissingMilesForm(forms.ModelForm):
    class Meta:
        from .models import ClaimMissingMiles, BANDARA_CHOICES, MASKAPAI_CHOICES, KELAS_KABIN_CHOICES
        model = ClaimMissingMiles
        fields = [
            "maskapai",
            "bandara_asal",
            "bandara_tujuan",
            "tanggal_penerbangan",
            "flight_number",
            "nomor_tiket",
            "kelas_kabin",
            "pnr",
        ]
        widgets = {
            "tanggal_penerbangan": forms.DateInput(attrs={"type": "date"}),
        }


class TransferForm(forms.Form):
    email_penerima = forms.EmailField(label="Email Member Penerima")
    jumlah = forms.IntegerField(label="Jumlah Miles", min_value=1)
    catatan = forms.CharField(
        label="Catatan (opsional)", required=False, widget=forms.Textarea(attrs={"rows": 3})
    )

    def __init__(self, pengirim, *args, **kwargs):
        self.pengirim = pengirim
        super().__init__(*args, **kwargs)

    def clean_email_penerima(self):
        email = self.cleaned_data["email_penerima"].lower()
        if email == self.pengirim.email:
            raise forms.ValidationError("Anda tidak dapat mentransfer miles ke diri sendiri.")
        if not User.objects.filter(email=email, role=User.Role.MEMBER).exists():
            raise forms.ValidationError("Email tidak terdaftar sebagai member aktif.")
        return email

    def clean_jumlah(self):
        jumlah = self.cleaned_data["jumlah"]
        try:
            profile = self.pengirim.member_profile
        except Exception:
            raise forms.ValidationError("Profil member tidak ditemukan.")
        if jumlah > profile.award_miles:
            raise forms.ValidationError(
                f"Award miles tidak mencukupi. Tersedia: {profile.award_miles} miles."
            )
        return jumlah
