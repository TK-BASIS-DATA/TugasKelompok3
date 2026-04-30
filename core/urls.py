from django.urls import path

from . import views

urlpatterns = [
    path("", views.auth_page, name="auth_page"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("logout/", views.logout_view, name="logout"),
    path("pengaturan-profile/", views.profile_settings_view, name="profile_settings"),
    path("member/identitas-saya/", views.member_page, {"title": "Identitas Saya"}, name="member_identitas"),
    path("member/klaim-miles/", views.klaim_miles_view, name="member_klaim"),
    path("member/transfer-miles/", views.transfer_miles_view, name="member_transfer"),
    path("member/redeem-miles/", views.member_redeem_view, name="member_redeem"),
    path("member/beli-package/", views.member_package_view, name="member_package"),
    path("member/info-tier/", views.member_tier_view, name="member_tier"),
    path("staf/kelola-member/", views.staff_page, {"title": "Kelola Member"}, name="staf_kelola_member"),
    path("staf/kelola-klaim/", views.kelola_klaim_view, name="staf_kelola_klaim"),
    path(
        "staf/kelola-hadiah-penyedia/",
        views.hadiah_list_view,
        name="staf_kelola_hadiah",
    ),
    path("staf/kelola-hadiah-penyedia/tambah/", views.hadiah_create_view, name="staf_tambah_hadiah"),
    path(
        "staf/kelola-hadiah-penyedia/<str:kode_hadiah>/ubah/",
        views.hadiah_update_view,
        name="staf_ubah_hadiah",
    ),
    path(
        "staf/kelola-hadiah-penyedia/<str:kode_hadiah>/hapus/",
        views.hadiah_delete_view,
        name="staf_hapus_hadiah",
    ),
    path("staf/kelola-mitra/", views.mitra_list_view, name="staf_kelola_mitra"),
    path("staf/kelola-mitra/tambah/", views.mitra_create_view, name="staf_tambah_mitra"),
    path("staf/kelola-mitra/<str:email_mitra>/ubah/", views.mitra_update_view, name="staf_ubah_mitra"),
    path("staf/kelola-mitra/<str:email_mitra>/hapus/", views.mitra_delete_view, name="staf_hapus_mitra"),
    path(
        "staf/laporan-transaksi/",
        views.staf_laporan_transaksi_view,
        name="staf_laporan_transaksi",
    ),
    path("pengaturan-profile/", views.profile_settings_view, name="profile_settings"),
]