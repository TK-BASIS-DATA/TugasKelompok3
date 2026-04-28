from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import (
    CustomPasswordChangeForm,
    LoginForm,
    MemberRegistrationForm,
    ProfileUpdateForm,
    StaffMaskapaiForm,
    StaffRegistrationForm,
)
from .models import ClaimMissingMiles, MemberProfile, MilesTransaction, StaffProfile, User


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
    if request.user.is_authenticated:
        return redirect("dashboard")

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
                return redirect("dashboard")

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


@login_required
def dashboard_view(request):
    context = {
        "user_obj": request.user,
        "full_name": request.user.full_name,
        "contact": f"{request.user.country_code} {request.user.mobile_number}",
    }

    if request.user.role == User.Role.MEMBER:
        member_profile = getattr(request.user, "member_profile", None)
        transactions = MilesTransaction.objects.filter(member=request.user)[:5]
        context.update(
            {
                "member_profile": member_profile,
                "transactions": transactions,
            }
        )

    if request.user.role == User.Role.STAF:
        staff_profile = getattr(request.user, "staff_profile", None)
        pending_claims = ClaimMissingMiles.objects.filter(
            status_penerimaan=ClaimMissingMiles.Status.MENUNGGU
        ).count()
        approved_by_me = ClaimMissingMiles.objects.filter(
            email_staf=request.user,
            status_penerimaan=ClaimMissingMiles.Status.DISETUJUI,
        ).count()
        rejected_by_me = ClaimMissingMiles.objects.filter(
            email_staf=request.user,
            status_penerimaan=ClaimMissingMiles.Status.DITOLAK,
        ).count()

        context.update(
            {
                "staff_profile": staff_profile,
                "pending_claims": pending_claims,
                "approved_by_me": approved_by_me,
                "rejected_by_me": rejected_by_me,
            }
        )

    return render(request, "core/dashboard.html", context)


@login_required
def profile_settings_view(request):
    user_form = ProfileUpdateForm(instance=request.user)
    password_form = CustomPasswordChangeForm(user=request.user)
    staff_form = None

    if request.user.role == User.Role.STAF:
        staff_form = StaffMaskapaiForm(instance=request.user.staff_profile)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_profile":
            user_form = ProfileUpdateForm(request.POST, instance=request.user)
            if request.user.role == User.Role.STAF:
                staff_form = StaffMaskapaiForm(request.POST, instance=request.user.staff_profile)
                if user_form.is_valid() and staff_form.is_valid():
                    user_form.save()
                    staff_form.save()
                    messages.success(request, "Profil berhasil diperbarui.")
                    return redirect("profile_settings")
            else:
                if user_form.is_valid():
                    user_form.save()
                    messages.success(request, "Profil berhasil diperbarui.")
                    return redirect("profile_settings")

        if action == "change_password":
            password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password berhasil diperbarui.")
                return redirect("profile_settings")

    context = {
        "user_form": user_form,
        "password_form": password_form,
    }

    if request.user.role == User.Role.MEMBER:
        context["member_profile"] = request.user.member_profile

    if request.user.role == User.Role.STAF:
        context["staff_profile"] = request.user.staff_profile
        context["staff_form"] = staff_form

    return render(request, "core/profile_settings.html", context)


@login_required
def member_page(request, title):
    if request.user.role != User.Role.MEMBER:
        messages.error(request, "Halaman ini khusus member.")
        return redirect("dashboard")
    return render(request, "core/placeholder.html", {"title": title})


@login_required
def staff_page(request, title):
    if request.user.role != User.Role.STAF:
        messages.error(request, "Halaman ini khusus staf.")
        return redirect("dashboard")
    return render(request, "core/placeholder.html", {"title": title})
