from django.urls import path

from . import views

urlpatterns = [
    path("", views.auth_page, name="auth_page"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("logout/", views.logout_view, name="logout"),
    path("pengaturan-profile/", views.profile_settings_view, name="profile_settings"),
    path("member/identitas-saya/", views.member_page, {"title": "Identitas Saya"}, name="member_identitas"),
    path("member/klaim-miles/", views.member_page, {"title": "Klaim Miles"}, name="member_klaim"),
    path("member/transfer-miles/", views.member_page, {"title": "Transfer Miles"}, name="member_transfer"),
    path("member/redeem-miles/", views.member_page, {"title": "Redeem Miles"}, name="member_redeem"),
    path("member/beli-package/", views.member_page, {"title": "Beli Package"}, name="member_package"),
    path("member/info-tier/", views.member_page, {"title": "Info Tier"}, name="member_tier"),
    path("staf/kelola-member/", views.staff_page, {"title": "Kelola Member"}, name="staf_kelola_member"),
    path("staf/kelola-klaim/", views.staff_page, {"title": "Kelola Klaim"}, name="staf_kelola_klaim"),
    path(
        "staf/kelola-hadiah-penyedia/",
        views.staff_page,
        {"title": "Kelola Hadiah dan Penyedia"},
        name="staf_kelola_hadiah",
    ),
    path("staf/kelola-mitra/", views.staff_page, {"title": "Kelola Mitra"}, name="staf_kelola_mitra"),
    path(
        "staf/laporan-transaksi/",
        views.staff_page,
        {"title": "Laporan Transaksi"},
        name="staf_laporan_transaksi",
    ),
]
