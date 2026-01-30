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
    wallet_metamask_bsc = models.CharField(max_length=255, unique=True)

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

    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.status}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

