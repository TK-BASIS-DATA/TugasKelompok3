from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import HadiahForm, MitraForm
from .models import (
    AwardMilesPackage,
    Hadiah,
    MemberProfile,
    MilesTransaction,
    Mitra,
    PembelianPackage,
    Penyedia,
    RedeemHadiah,
    StaffProfile,
    User,
)


class StaffCrudBaseTestCase(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            email="staf@aeromiles.test",
            password="Password123!",
            role=User.Role.STAF,
            salutation="Mr",
            first_mid_name="Staf",
            last_name="Tester",
            country_code="+62",
            mobile_number="08123456789",
            kewarganegaraan="Indonesia",
        )
        StaffProfile.objects.create(
            user=self.staff_user,
            id_staf="S0001",
            kode_maskapai="M1",
        )
        self.client.force_login(self.staff_user)


class MemberFeatureBaseTestCase(TestCase):
    def setUp(self):
        self.member_user = User.objects.create_user(
            email="member@aeromiles.test",
            password="Password123!",
            role=User.Role.MEMBER,
            salutation="Ms",
            first_mid_name="Member",
            last_name="Tester",
            country_code="+62",
            mobile_number="08123456780",
            kewarganegaraan="Indonesia",
        )
        self.member_profile = MemberProfile.objects.create(
            user=self.member_user,
            nomor_member="M0001",
            tier="Blue",
            total_miles=10000,
            award_miles=10000,
        )
        self.client.force_login(self.member_user)


class HadiahFormTest(TestCase):
    def test_hadiah_form_rejects_invalid_period(self):
        penyedia = Penyedia.objects.create(
            id_penyedia="P0001",
            nama="Garuda Nusantara",
            jenis=Penyedia.Jenis.MASKAPAI,
        )
        form = HadiahForm(
            data={
                "nama": "Voucher Lounge",
                "penyedia": penyedia.pk,
                "miles": 1000,
                "deskripsi": "Akses lounge domestik.",
                "valid_start_date": "2026-05-10",
                "program_end": "2026-05-01",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("Tanggal mulai valid tidak boleh melewati tanggal akhir program.", form.non_field_errors())


class MitraFormTest(TestCase):
    def test_mitra_form_rejects_future_collaboration_date(self):
        tomorrow = timezone.localdate() + timezone.timedelta(days=1)
        form = MitraForm(
            data={
                "email_mitra": "mitra@example.com",
                "nama_mitra": "Hotel Nusantara",
                "tanggal_kerja_sama": tomorrow,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("Tanggal kerja sama tidak boleh di masa depan.", form.errors["tanggal_kerja_sama"])


class MitraCrudViewTest(StaffCrudBaseTestCase):
    def test_create_mitra_also_creates_penyedia(self):
        response = self.client.post(
            reverse("staf_tambah_mitra"),
            data={
                "email_mitra": "mitra@example.com",
                "nama_mitra": "Hotel Nusantara",
                "tanggal_kerja_sama": "2026-04-01",
            },
        )

        self.assertRedirects(response, reverse("staf_kelola_mitra"))
        mitra = Mitra.objects.get(email_mitra="mitra@example.com")
        self.assertEqual(mitra.nama_mitra, "Hotel Nusantara")
        self.assertEqual(mitra.penyedia.jenis, Penyedia.Jenis.MITRA)
        self.assertEqual(mitra.penyedia.nama, "Hotel Nusantara")

    def test_delete_mitra_also_deletes_related_hadiah(self):
        penyedia = Penyedia.objects.create(
            id_penyedia="P0001",
            nama="Hotel Nusantara",
            jenis=Penyedia.Jenis.MITRA,
        )
        mitra = Mitra.objects.create(
            email_mitra="mitra@example.com",
            penyedia=penyedia,
            nama_mitra="Hotel Nusantara",
            tanggal_kerja_sama=timezone.localdate(),
        )
        hadiah = Hadiah.objects.create(
            kode_hadiah="H0001",
            nama="Voucher Hotel",
            deskripsi="Potongan menginap.",
            penyedia=penyedia,
            miles=5000,
            valid_start_date=timezone.localdate(),
            program_end=timezone.localdate(),
        )

        response = self.client.post(reverse("staf_hapus_mitra", args=[mitra.email_mitra]))

        self.assertRedirects(response, reverse("staf_kelola_mitra"))
        self.assertFalse(Mitra.objects.filter(email_mitra=mitra.email_mitra).exists())
        self.assertFalse(Penyedia.objects.filter(pk=penyedia.pk).exists())
        self.assertFalse(Hadiah.objects.filter(pk=hadiah.pk).exists())


class HadiahCrudViewTest(StaffCrudBaseTestCase):
    def setUp(self):
        super().setUp()
        self.penyedia = Penyedia.objects.create(
            id_penyedia="P0001",
            nama="Garuda Nusantara",
            jenis=Penyedia.Jenis.MASKAPAI,
        )

    def test_create_hadiah_generates_code(self):
        response = self.client.post(
            reverse("staf_tambah_hadiah"),
            data={
                "nama": "Voucher Lounge",
                "penyedia": self.penyedia.pk,
                "miles": 1500,
                "deskripsi": "Akses lounge domestik.",
                "valid_start_date": "2026-04-01",
                "program_end": "2026-05-01",
            },
        )

        self.assertRedirects(response, reverse("staf_kelola_hadiah"))
        hadiah = Hadiah.objects.get(nama="Voucher Lounge")
        self.assertEqual(hadiah.kode_hadiah, "H0001")

    def test_delete_hadiah_is_rejected_when_program_not_finished(self):
        hadiah = Hadiah.objects.create(
            kode_hadiah="H0001",
            nama="Voucher Lounge",
            deskripsi="Akses lounge domestik.",
            penyedia=self.penyedia,
            miles=1500,
            valid_start_date=timezone.localdate(),
            program_end=timezone.localdate() + timezone.timedelta(days=5),
        )

        response = self.client.post(reverse("staf_hapus_hadiah", args=[hadiah.kode_hadiah]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Hadiah.objects.filter(pk=hadiah.pk).exists())
        messages = list(response.context["messages"])
        self.assertTrue(any("hanya dapat dihapus" in str(message) for message in messages))

    def test_delete_hadiah_succeeds_when_program_is_expired(self):
        hadiah = Hadiah.objects.create(
            kode_hadiah="H0001",
            nama="Voucher Lounge",
            deskripsi="Akses lounge domestik.",
            penyedia=self.penyedia,
            miles=1500,
            valid_start_date=timezone.localdate() - timezone.timedelta(days=10),
            program_end=timezone.localdate() - timezone.timedelta(days=1),
        )

        response = self.client.post(reverse("staf_hapus_hadiah", args=[hadiah.kode_hadiah]))

        self.assertRedirects(response, reverse("staf_kelola_hadiah"))
        self.assertFalse(Hadiah.objects.filter(pk=hadiah.pk).exists())


class MemberRedeemHadiahViewTest(MemberFeatureBaseTestCase):
    def setUp(self):
        super().setUp()
        self.penyedia = Penyedia.objects.create(
            id_penyedia="P0001",
            nama="Garuda Nusantara",
            jenis=Penyedia.Jenis.MASKAPAI,
        )
        self.hadiah = Hadiah.objects.create(
            kode_hadiah="H0001",
            nama="Voucher Lounge",
            deskripsi="Akses lounge domestik.",
            penyedia=self.penyedia,
            miles=1500,
            valid_start_date=timezone.localdate() - timezone.timedelta(days=1),
            program_end=timezone.localdate() + timezone.timedelta(days=5),
        )

    def test_member_can_read_and_create_redeem_hadiah(self):
        response = self.client.get(reverse("member_redeem"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Redeem Hadiah")

        response = self.client.post(
            reverse("member_redeem"),
            data={"hadiah": self.hadiah.pk, "catatan": "Kirim voucher via email."},
        )

        self.assertRedirects(response, reverse("member_redeem"))
        redeem = RedeemHadiah.objects.get(member=self.member_user)
        self.assertEqual(redeem.hadiah, self.hadiah)
        self.member_profile.refresh_from_db()
        self.assertEqual(self.member_profile.award_miles, 8500)
        self.assertTrue(
            MilesTransaction.objects.filter(
                member=self.member_user,
                deskripsi__icontains="Redeem hadiah",
                miles_delta=-1500,
            ).exists()
        )


class MemberPackageViewTest(MemberFeatureBaseTestCase):
    def test_member_can_read_and_buy_award_miles_package(self):
        package = AwardMilesPackage.objects.create(
            kode_package="PKG999",
            nama="Test Miles",
            deskripsi="Paket test.",
            miles=3000,
            harga_idr=150000,
        )

        response = self.client.get(reverse("member_package"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Beli Award Miles Package")

        response = self.client.post(reverse("member_package"), data={"kode_package": package.pk})

        self.assertRedirects(response, reverse("member_package"))
        pembelian = PembelianPackage.objects.get(member=self.member_user, package=package)
        self.assertEqual(pembelian.miles_diterima, 3000)
        self.member_profile.refresh_from_db()
        self.assertEqual(self.member_profile.award_miles, 13000)
        self.assertEqual(self.member_profile.total_miles, 13000)


class MemberTierViewTest(MemberFeatureBaseTestCase):
    def test_member_can_read_tier_information(self):
        response = self.client.get(reverse("member_tier"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Informasi Tier")
        self.assertContains(response, "Blue")


class StaffLaporanTransaksiViewTest(StaffCrudBaseTestCase):
    def setUp(self):
        super().setUp()
        self.member_user = User.objects.create_user(
            email="member@aeromiles.test",
            password="Password123!",
            role=User.Role.MEMBER,
            salutation="Mr",
            first_mid_name="Member",
            last_name="Report",
            country_code="+62",
            mobile_number="08123456781",
            kewarganegaraan="Indonesia",
        )
        MemberProfile.objects.create(
            user=self.member_user,
            nomor_member="M0001",
            tier="Blue",
            total_miles=5000,
            award_miles=5000,
        )
        self.transaction = MilesTransaction.objects.create(
            member=self.member_user,
            deskripsi="Bonus test",
            miles_delta=5000,
        )

    def test_staff_can_read_and_delete_miles_transaction(self):
        response = self.client.get(reverse("staf_laporan_transaksi"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bonus test")

        response = self.client.post(
            reverse("staf_laporan_transaksi"),
            data={"action": "delete", "trx_id": self.transaction.pk},
        )

        self.assertRedirects(response, reverse("staf_laporan_transaksi"))
        self.assertFalse(MilesTransaction.objects.filter(pk=self.transaction.pk).exists())
