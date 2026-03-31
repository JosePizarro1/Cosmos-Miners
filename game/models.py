from django.conf import settings
from .models_cofres import *
from .models_rankings import *
from .models_planets import *
from .models_oil import *
from .models_trades import *
from .models_packs import *
from .models_blessings import *
from .models_alliances import *
from .models_gifts import *
from .models_market import *

from django.db import models
from django.utils import timezone
from decimal import Decimal
from .models_rankings import Season
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    wallet_metamask_bsc = models.CharField(max_length=255,null=True,blank=True, unique=True)

    # Cosmos GOLD balance for the user
    cosmos_gold = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    black_gold = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Points earned from planets
    points = models.IntegerField(default=0)

    # Alliance fields
    alliance = models.ForeignKey('game.Alliance', on_delete=models.SET_NULL, null=True, blank=True, related_name='members_profiles')
    alliance_cooldown_until = models.DateTimeField(null=True, blank=True)

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
        profile, _ = Profile.objects.get_or_create(user=instance)

class MinerRarity(models.TextChoices):
    COMMON = "common", "Común"
    UNCOMMON = "uncommon", "Poco común"
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

    points_multiplier = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('1.00'),
        help_text="Multiplicador de puntos de planeta. 1=normal, 2=doble, etc."
    )
    season = models.ForeignKey(
        Season, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='miner_types',
        help_text="Temporada a la que aplica el multiplicador de puntos"
    )

    is_active = models.BooleanField(default=True)
    is_free = models.BooleanField(default=False)

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
    UNCOMMON = "uncommon", "Poco común"
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

    speed = models.PositiveIntegerField(
        help_text="Velocidad del transporte (impacta tiempo de viaje)"
    )

    is_active = models.BooleanField(default=True)
    is_free = models.BooleanField(default=False)

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


class ToolRarity(models.TextChoices):
    COMMON = "common", "Común"
    UNCOMMON = "uncommon", "Poco común"
    RARE = "rare", "Raro"
    EPIC = "epic", "Épico"
    LEGENDARY = "legendary", "Legendario"

class ToolType(models.Model):
    name = models.CharField(max_length=100)

    image = models.ImageField(
        upload_to="tools/",
        null=True,
        blank=True
    )

    rarity = models.CharField(
        max_length=20,
        choices=ToolRarity.choices
    )

    bonus_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("100.00"),
        help_text="Bonus de producción en %. Ej: 100=x1, 200=x2 (duplica rango mineral)"
    )

    is_active = models.BooleanField(default=True)
    is_free = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_rarity_display()})"
class ToolStatus(models.TextChoices):
    IDLE = "idle", "Disponible"
    TRAVELING = "traveling", "En uso"
class UserTool(models.Model):
    owner = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="tools"
    )

    tool_type = models.ForeignKey(
        ToolType,
        on_delete=models.PROTECT,
        related_name="user_tools"
    )

    status = models.CharField(
        max_length=20,
        choices=ToolStatus.choices,
        default=ToolStatus.IDLE
    )

    obtained_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tool_type.name} - {self.owner.user.username}"


class RegistrationReward(models.Model):
    class RewardType(models.TextChoices):
        MINER = "miner", "Minero"
        TRANSPORT = "transport", "Transporte"
        TOOL = "tool", "Herramienta"
        GOLD = "gold", "Cosmos Gold"

    reward_type = models.CharField(max_length=20, choices=RewardType.choices)
    
    miner_type = models.ForeignKey(MinerType, on_delete=models.SET_NULL, null=True, blank=True)
    transport_type = models.ForeignKey(TransportType, on_delete=models.SET_NULL, null=True, blank=True)
    tool_type = models.ForeignKey(ToolType, on_delete=models.SET_NULL, null=True, blank=True)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Para Gold o cantidad")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.reward_type == self.RewardType.MINER:
            return f"Regalo: Minero {self.miner_type.name if self.miner_type else '???'}"
        if self.reward_type == self.RewardType.TRANSPORT:
            return f"Regalo: Transporte {self.transport_type.name if self.transport_type else '???'}"
        if self.reward_type == self.RewardType.TOOL:
            return f"Regalo: Herramienta {self.tool_type.name if self.tool_type else '???'}"
        return f"Regalo: {self.amount} Cosmos Gold"

@receiver(post_save, sender=User)
def grant_registration_rewards(sender, instance, created, **kwargs):
    if created:
        # We need to ensure Profile is created first or use its signal
        # Since create_user_profile (at top) creates the profile, we can use it here.
        profile = instance.profile
        
        # Grant Starter Pack Items
        rewards = RegistrationReward.objects.filter(is_active=True)
        for r in rewards:
            if r.reward_type == RegistrationReward.RewardType.MINER and r.miner_type:
                UserMiner.objects.create(owner=profile, miner_type=r.miner_type)
            elif r.reward_type == RegistrationReward.RewardType.TRANSPORT and r.transport_type:
                UserTransport.objects.create(owner=profile, transport_type=r.transport_type)
            elif r.reward_type == RegistrationReward.RewardType.TOOL and r.tool_type:
                UserTool.objects.create(owner=profile, tool_type=r.tool_type)
            elif r.reward_type == RegistrationReward.RewardType.GOLD:
                profile.cosmos_gold += r.amount
                profile.save()
