from django.conf import settings
from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    wallet_metamask_bsc = models.CharField(max_length=255,null=True,blank=True, unique=True)

    # Cosmos GOLD balance for the user
    cosmos_gold = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class WithdrawalRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_ACCEPTED, 'Aceptado'),
        (STATUS_REJECTED, 'Rechazado'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)

    # when processed (accepted/rejected)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='processed_withdrawals')
    balance_before = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="User balance before withdrawal"
    )

    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="User balance after withdrawal"
    )
    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.status}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

class MinerRarity(models.TextChoices):
    COMMON = "common", "Común"
    RARE = "rare", "Raro"
    EPIC = "epic", "Épico"
    LEGENDARY = "legendary", "Legendario"


class MinerType(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="miners/", null=True, blank=True)

    rarity = models.CharField(
        max_length=20,
        choices=MinerRarity.choices
    )

    attempts = models.PositiveIntegerField(
        help_text="Cantidad de intentos de minado por viaje"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_rarity_display()})"

class MinerStatus(models.TextChoices):
    IDLE = "idle", "Disponible"
    TRAVELING = "traveling", "Viajando"


class UserMiner(models.Model):
    owner = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="miners"
    )

    miner_type = models.ForeignKey(
        MinerType,
        on_delete=models.PROTECT,
        related_name="user_miners"
    )

    status = models.CharField(
        max_length=20,
        choices=MinerStatus.choices,
        default=MinerStatus.IDLE
    )

    obtained_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.miner_type.name} - {self.owner.user.username}"

class TransportRarity(models.TextChoices):
    COMMON = "common", "Común"
    RARE = "rare", "Raro"
    EPIC = "epic", "Épico"
    LEGENDARY = "legendary", "Legendario"


class TransportType(models.Model):
    name = models.CharField(max_length=100)

    image = models.ImageField(
        upload_to="transports/",
        null=True,
        blank=True
    )

    rarity = models.CharField(
        max_length=20,
        choices=TransportRarity.choices
    )

    capacity = models.PositiveIntegerField(
        help_text="Cantidad máxima de recursos que puede transportar"
    )

    speed = models.PositiveIntegerField(
        help_text="Velocidad del transporte (impacta tiempo de viaje)"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_rarity_display()})"



class TransportStatus(models.TextChoices):
    IDLE = "idle", "Disponible"
    TRAVELING = "traveling", "En viaje"


class UserTransport(models.Model):
    owner = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="transports"
    )

    transport_type = models.ForeignKey(
        TransportType,
        on_delete=models.PROTECT,
        related_name="user_transports"
    )

    status = models.CharField(
        max_length=20,
        choices=TransportStatus.choices,
        default=TransportStatus.IDLE
    )

    obtained_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transport_type.name} - {self.owner.user.username}"
