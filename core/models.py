from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

MASKAPAI_CHOICES = [
    ("M1", "M1 - Garuda Nusantara"),
    ("M2", "M2 - Langit Air"),
    ("M3", "M3 - Samudra Wings"),
    ("M4", "M4 - Borneo Flight"),
    ("M5", "M5 - Cakrawala Air"),
]


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be provided")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        MEMBER = "member", "Member"
        STAF = "staf", "Staf"

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    salutation = models.CharField(max_length=10, default="Mr")
    first_mid_name = models.CharField(max_length=100, default="User")
    last_name = models.CharField(max_length=100, default="Aero")
    country_code = models.CharField(max_length=5, default="+62")
    mobile_number = models.CharField(max_length=20, default="0000000000")
    tanggal_lahir = models.DateField(default=timezone.localdate)
    kewarganegaraan = models.CharField(max_length=50, default="Indonesia")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.salutation} {self.first_mid_name} {self.last_name}".strip()


class MemberProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="member_profile")
    nomor_member = models.CharField(max_length=20, unique=True)
    tier = models.CharField(max_length=20, default="Blue")
    tanggal_bergabung = models.DateField(default=timezone.localdate)
    total_miles = models.IntegerField(default=0)
    award_miles = models.IntegerField(default=0)

    def __str__(self):
        return self.nomor_member


class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="staff_profile")
    id_staf = models.CharField(max_length=20, unique=True)
    kode_maskapai = models.CharField(max_length=10, choices=MASKAPAI_CHOICES)

    def __str__(self):
        return self.id_staf


class MilesTransaction(models.Model):
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name="miles_transactions")
    deskripsi = models.CharField(max_length=255)
    miles_delta = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]


BANDARA_CHOICES = [
    ("CGK", "CGK - Soekarno-Hatta, Jakarta"),
    ("DPS", "DPS - Ngurah Rai, Bali"),
    ("SUB", "SUB - Juanda, Surabaya"),
    ("KUL", "KUL - Kuala Lumpur International"),
    ("SIN", "SIN - Changi, Singapore"),
    ("NRT", "NRT - Narita, Tokyo"),
    ("BKK", "BKK - Suvarnabhumi, Bangkok"),
    ("HKG", "HKG - Hong Kong International"),
    ("SYD", "SYD - Kingsford Smith, Sydney"),
    ("MEL", "MEL - Melbourne Airport"),
    ("AMS", "AMS - Schiphol, Amsterdam"),
    ("LHR", "LHR - Heathrow, London"),
    ("DXB", "DXB - Dubai International"),
    ("DOH", "DOH - Hamad, Doha"),
    ("ICN", "ICN - Incheon, Seoul"),
]

KELAS_KABIN_CHOICES = [
    ("Economy", "Economy"),
    ("Business", "Business"),
    ("First", "First"),
]


class ClaimMissingMiles(models.Model):
    class Status(models.TextChoices):
        MENUNGGU = "Menunggu", "Menunggu"
        DISETUJUI = "Disetujui", "Disetujui"
        DITOLAK = "Ditolak", "Ditolak"

    email_member = models.ForeignKey(User, on_delete=models.CASCADE, related_name="claims")
    email_staf = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="claims_handled",
        null=True,
        blank=True,
    )
    maskapai = models.CharField(max_length=10, choices=MASKAPAI_CHOICES, default="M1")
    bandara_asal = models.CharField(max_length=3, choices=BANDARA_CHOICES, default="CGK")
    bandara_tujuan = models.CharField(max_length=3, choices=BANDARA_CHOICES, default="DPS")
    tanggal_penerbangan = models.DateField(default=timezone.localdate)
    flight_number = models.CharField(max_length=10, default="")
    nomor_tiket = models.CharField(max_length=20, default="")
    kelas_kabin = models.CharField(max_length=20, choices=KELAS_KABIN_CHOICES, default="Economy")
    pnr = models.CharField(max_length=10, default="")
    status_penerimaan = models.CharField(max_length=20, choices=Status.choices, default=Status.MENUNGGU)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["email_member", "flight_number", "tanggal_penerbangan", "nomor_tiket"],
                name="unique_claim_per_flight",
            )
        ]

    def __str__(self):
        return f"CLM-{self.pk:03d}"

    @property
    def claim_id(self):
        return f"CLM-{self.pk:03d}"


class Transfer(models.Model):
    email_member_1 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transfers_sent"
    )
    email_member_2 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transfers_received"
    )
    timestamp = models.DateTimeField(default=timezone.now)
    jumlah = models.IntegerField()
    catatan = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Transfer {self.jumlah} miles dari {self.email_member_1} ke {self.email_member_2}"
