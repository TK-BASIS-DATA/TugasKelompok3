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


class Penyedia(models.Model):
    class Jenis(models.TextChoices):
        MASKAPAI = "maskapai", "Maskapai"
        MITRA = "mitra", "Mitra"

    id_penyedia = models.CharField(max_length=20, primary_key=True)
    nama = models.CharField(max_length=100)
    jenis = models.CharField(max_length=20, choices=Jenis.choices)

    class Meta:
        ordering = ["id_penyedia"]

    def __str__(self):
        return f"{self.id_penyedia} - {self.nama}"


class Mitra(models.Model):
    email_mitra = models.EmailField(primary_key=True)
    penyedia = models.OneToOneField(Penyedia, on_delete=models.CASCADE, related_name="mitra")
    nama_mitra = models.CharField(max_length=100)
    tanggal_kerja_sama = models.DateField(default=timezone.localdate)

    class Meta:
        ordering = ["nama_mitra", "email_mitra"]

    def __str__(self):
        return self.nama_mitra


class Hadiah(models.Model):
    kode_hadiah = models.CharField(max_length=20, primary_key=True)
    nama = models.CharField(max_length=100)
    deskripsi = models.TextField()
    penyedia = models.ForeignKey(Penyedia, on_delete=models.CASCADE, related_name="hadiah")
    miles = models.PositiveIntegerField()
    valid_start_date = models.DateField()
    program_end = models.DateField()

    class Meta:
        ordering = ["nama", "kode_hadiah"]

    def __str__(self):
        return f"{self.kode_hadiah} - {self.nama}"

    @property
    def is_active(self):
        today = timezone.localdate()
        return self.valid_start_date <= today <= self.program_end

    @property
    def is_expired(self):
        return self.program_end < timezone.localdate()


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
    status_penerimaan = models.CharField(max_length=20, choices=Status.choices, default=Status.MENUNGGU)
    created_at = models.DateTimeField(default=timezone.now)
