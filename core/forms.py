from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm
from django.utils import timezone

from .models import Hadiah, MASKAPAI_CHOICES, Mitra, Penyedia, StaffProfile, User


def _apply_input_classes(fields):
    base_class = "w-full rounded-2xl border border-aero-cloud bg-white px-4 py-3 text-sm text-aero-ink outline-none transition focus:border-aero-mint focus:ring-2 focus:ring-aero-cloud"
    for field in fields.values():
        existing_class = field.widget.attrs.get("class", "")
        field.widget.attrs["class"] = f"{existing_class} {base_class}".strip()


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


class HadiahForm(forms.ModelForm):
    class Meta:
        model = Hadiah
        fields = [
            "nama",
            "penyedia",
            "miles",
            "deskripsi",
            "valid_start_date",
            "program_end",
        ]
        widgets = {
            "deskripsi": forms.Textarea(attrs={"rows": 4}),
            "valid_start_date": forms.DateInput(attrs={"type": "date"}),
            "program_end": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["penyedia"].queryset = Penyedia.objects.order_by("jenis", "nama")
        _apply_input_classes(self.fields)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("valid_start_date")
        end_date = cleaned_data.get("program_end")
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Tanggal mulai valid tidak boleh melewati tanggal akhir program.")
        return cleaned_data


class MitraForm(forms.ModelForm):
    class Meta:
        model = Mitra
        fields = ["email_mitra", "nama_mitra", "tanggal_kerja_sama"]
        widgets = {
            "tanggal_kerja_sama": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["email_mitra"].disabled = True
        _apply_input_classes(self.fields)

    def clean_tanggal_kerja_sama(self):
        tanggal_kerja_sama = self.cleaned_data["tanggal_kerja_sama"]
        if tanggal_kerja_sama > timezone.localdate():
            raise forms.ValidationError("Tanggal kerja sama tidak boleh di masa depan.")
        return tanggal_kerja_sama


class HadiahFilterForm(forms.Form):
    penyedia = forms.ModelChoiceField(
        queryset=Penyedia.objects.none(),
        required=False,
        empty_label="Semua penyedia",
    )
    status = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Semua status"),
            ("aktif", "Aktif"),
            ("nonaktif", "Tidak aktif"),
            ("kedaluwarsa", "Kedaluwarsa"),
        ],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["penyedia"].queryset = Penyedia.objects.order_by("jenis", "nama")
        _apply_input_classes(self.fields)
