from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    CustomPasswordChangeForm,
    HadiahFilterForm,
    HadiahForm,
    LoginForm,
    MemberRegistrationForm,
    MitraForm,
    ProfileUpdateForm,
    StaffMaskapaiForm,
    StaffRegistrationForm,
)
from .models import ClaimMissingMiles, Hadiah, MemberProfile, MilesTransaction, Mitra, Penyedia, StaffProfile, User

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


def _next_provider_id():
    last_provider = Penyedia.objects.order_by("-id_penyedia").first()
    if not last_provider:
        return "P0001"
    last_num = int(last_provider.id_penyedia[1:])
    return f"P{last_num + 1:04d}"


def _next_reward_code():
    last_reward = Hadiah.objects.order_by("-kode_hadiah").first()
    if not last_reward:
        return "H0001"
    last_num = int(last_reward.kode_hadiah[1:])
    return f"H{last_num + 1:04d}"


def _ensure_maskapai_providers():
    for kode, label in StaffProfile._meta.get_field("kode_maskapai").choices:
        Penyedia.objects.get_or_create(
            nama=label,
            jenis=Penyedia.Jenis.MASKAPAI,
            defaults={"id_penyedia": _next_provider_id()},
        )


def _staff_only(request):
    if request.user.role != User.Role.STAF:
        messages.error(request, "Halaman ini khusus staf.")
        return False
    return True


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
        "email": request.user.email,
        "country_code": request.user.country_code,
        "mobile_number": request.user.mobile_number,
    }

    if request.user.role == User.Role.MEMBER:
        member_profile = getattr(request.user, "member_profile", None)
        recent_transactions = MilesTransaction.objects.filter(member=request.user)[:5]
        totals = MilesTransaction.objects.filter(member=request.user).aggregate(
            total_miles=Coalesce(Sum("miles_delta"), 0),
            award_miles=Coalesce(Sum("miles_delta", filter=Q(miles_delta__gt=0)), 0),
        )
        context.update(
            {
                "member_profile": member_profile,
                "derived_total_miles": totals["total_miles"],
                "derived_award_miles": totals["award_miles"],
                "recent_transactions": recent_transactions,
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
    if not _staff_only(request):
        return redirect("dashboard")
    return render(request, "core/placeholder.html", {"title": title})


@login_required
def hadiah_list_view(request):
    if not _staff_only(request):
        return redirect("dashboard")

    _ensure_maskapai_providers()
    hadiah_qs = Hadiah.objects.select_related("penyedia").order_by("nama", "kode_hadiah")
    filter_form = HadiahFilterForm(request.GET or None)

    if filter_form.is_valid():
        penyedia = filter_form.cleaned_data.get("penyedia")
        status = filter_form.cleaned_data.get("status")

        if penyedia:
            hadiah_qs = hadiah_qs.filter(penyedia=penyedia)

        today = timezone.localdate()
        if status == "aktif":
            hadiah_qs = hadiah_qs.filter(valid_start_date__lte=today, program_end__gte=today)
        elif status == "nonaktif":
            hadiah_qs = hadiah_qs.filter(Q(valid_start_date__gt=today) | Q(program_end__lt=today))
        elif status == "kedaluwarsa":
            hadiah_qs = hadiah_qs.filter(program_end__lt=today)

    return render(
        request,
        "core/hadiah_list.html",
        {
            "title": "Kelola Hadiah dan Penyedia",
            "hadiah_list": hadiah_qs,
            "filter_form": filter_form,
        },
    )


@login_required
def hadiah_create_view(request):
    if not _staff_only(request):
        return redirect("dashboard")

    _ensure_maskapai_providers()
    form = HadiahForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        hadiah = form.save(commit=False)
        hadiah.kode_hadiah = _next_reward_code()
        hadiah.save()
        messages.success(request, f"Hadiah {hadiah.kode_hadiah} berhasil ditambahkan.")
        return redirect("staf_kelola_hadiah")

    return render(
        request,
        "core/hadiah_form.html",
        {
            "title": "Tambah Hadiah",
            "form": form,
            "submit_label": "Simpan Hadiah",
            "is_edit": False,
        },
    )


@login_required
def hadiah_update_view(request, kode_hadiah):
    if not _staff_only(request):
        return redirect("dashboard")

    _ensure_maskapai_providers()
    hadiah = get_object_or_404(Hadiah.objects.select_related("penyedia"), kode_hadiah=kode_hadiah)
    form = HadiahForm(request.POST or None, instance=hadiah)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Hadiah {hadiah.kode_hadiah} berhasil diperbarui.")
        return redirect("staf_kelola_hadiah")

    return render(
        request,
        "core/hadiah_form.html",
        {
            "title": "Ubah Hadiah",
            "form": form,
            "submit_label": "Perbarui Hadiah",
            "is_edit": True,
            "hadiah": hadiah,
        },
    )


@login_required
def hadiah_delete_view(request, kode_hadiah):
    if not _staff_only(request):
        return redirect("dashboard")

    hadiah = get_object_or_404(Hadiah, kode_hadiah=kode_hadiah)
    if request.method == "POST":
        if not hadiah.is_expired:
            messages.error(request, "Hadiah hanya dapat dihapus jika periode program sudah selesai.")
            return redirect("staf_kelola_hadiah")

        hadiah.delete()
        messages.success(request, f"Hadiah {kode_hadiah} berhasil dihapus.")
    return redirect("staf_kelola_hadiah")


@login_required
def mitra_list_view(request):
    if not _staff_only(request):
        return redirect("dashboard")

    mitra_list = Mitra.objects.select_related("penyedia").order_by("nama_mitra", "email_mitra")
    return render(
        request,
        "core/mitra_list.html",
        {
            "title": "Kelola Mitra",
            "mitra_list": mitra_list,
        },
    )


@login_required
def mitra_create_view(request):
    if not _staff_only(request):
        return redirect("dashboard")

    form = MitraForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            penyedia = Penyedia.objects.create(
                id_penyedia=_next_provider_id(),
                nama=form.cleaned_data["nama_mitra"],
                jenis=Penyedia.Jenis.MITRA,
            )
            mitra = form.save(commit=False)
            mitra.penyedia = penyedia
            mitra.save()

        messages.success(request, f"Mitra {mitra.nama_mitra} berhasil ditambahkan.")
        return redirect("staf_kelola_mitra")

    return render(
        request,
        "core/mitra_form.html",
        {
            "title": "Tambah Mitra",
            "form": form,
            "submit_label": "Simpan Mitra",
            "is_edit": False,
        },
    )


@login_required
def mitra_update_view(request, email_mitra):
    if not _staff_only(request):
        return redirect("dashboard")

    mitra = get_object_or_404(Mitra.objects.select_related("penyedia"), email_mitra=email_mitra)
    form = MitraForm(request.POST or None, instance=mitra)

    if request.method == "POST" and form.is_valid():
        mitra = form.save()
        mitra.penyedia.nama = mitra.nama_mitra
        mitra.penyedia.save(update_fields=["nama"])
        messages.success(request, f"Informasi mitra {mitra.nama_mitra} berhasil diperbarui.")
        return redirect("staf_kelola_mitra")

    return render(
        request,
        "core/mitra_form.html",
        {
            "title": "Ubah Mitra",
            "form": form,
            "submit_label": "Perbarui Mitra",
            "is_edit": True,
            "mitra": mitra,
        },
    )


@login_required
def mitra_delete_view(request, email_mitra):
    if not _staff_only(request):
        return redirect("dashboard")

    mitra = get_object_or_404(Mitra.objects.select_related("penyedia"), email_mitra=email_mitra)
    if request.method == "POST":
        nama_mitra = mitra.nama_mitra
        penyedia = mitra.penyedia
        penyedia.delete()
        messages.success(request, f"Mitra {nama_mitra} beserta hadiah terkait berhasil dihapus.")
    return redirect("staf_kelola_mitra")
