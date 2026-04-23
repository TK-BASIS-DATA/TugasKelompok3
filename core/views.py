from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import (
    LoginForm,
    MemberRegistrationForm,
    StaffRegistrationForm,
)
from .models import MemberProfile, MilesTransaction, StaffProfile, User


def _next_member_number():
    last_member = MemberProfile.objects.order_by("-nomor_member").first()
    if not last_member:
        return "M0001"
    last_num = int(last_member.nomor_member[1:])
    return f"M{last_num + 1:04d}"


def _next_staff_id():
    last_staff = StaffProfile.objects.order_by("-id_staf").first()
    if not last_staff:
        return "S0001"
    last_num = int(last_staff.id_staf[1:])
    return f"S{last_num + 1:04d}"


def auth_page(request):
    login_form = LoginForm(request=request)
    member_form = MemberRegistrationForm(prefix="member")
    staff_form = StaffRegistrationForm(prefix="staf")
    active_register = request.GET.get("role", "member")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "login":
            login_form = LoginForm(request=request, data=request.POST)
            if login_form.is_valid():
                login(request, login_form.get_user())
                messages.success(request, "Login berhasil.")
                return redirect("auth_page")

        if action == "register_member":
            active_register = "member"
            member_form = MemberRegistrationForm(request.POST, prefix="member")
            if member_form.is_valid():
                user = member_form.save(commit=False)
                user.role = User.Role.MEMBER
                user.set_password(member_form.cleaned_data["password"])
                user.save()

                member_profile = MemberProfile.objects.create(
                    user=user,
                    nomor_member=_next_member_number(),
                    tier="Blue",
                    tanggal_bergabung=timezone.localdate(),
                )

                MilesTransaction.objects.create(
                    member=user,
                    deskripsi=f"Registrasi member {member_profile.nomor_member}",
                    miles_delta=0,
                )

                messages.success(request, "Registrasi member berhasil. Silakan login.")
                return redirect("auth_page")

        if action == "register_staf":
            active_register = "staf"
            staff_form = StaffRegistrationForm(request.POST, prefix="staf")
            if staff_form.is_valid():
                user = staff_form.save(commit=False)
                user.role = User.Role.STAF
                user.set_password(staff_form.cleaned_data["password"])
                user.save()

                StaffProfile.objects.create(
                    user=user,
                    id_staf=_next_staff_id(),
                    kode_maskapai=staff_form.cleaned_data["kode_maskapai"],
                )

                messages.success(request, "Registrasi staf berhasil. Silakan login.")
                return redirect("auth_page")

    return render(
        request,
        "core/auth.html",
        {
            "login_form": login_form,
            "member_form": member_form,
            "staff_form": staff_form,
            "active_register": active_register,
        },
    )


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Anda telah logout.")
    return redirect("auth_page")
