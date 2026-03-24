from django.db import models
from decimal import Decimal

class OilCentralType(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="oil_centrals/", null=True, blank=True)
    price_gold = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Life range (days)
    min_life_days = models.PositiveIntegerField(default=10)
    max_life_days = models.PositiveIntegerField(default=30)
    
    # Barrels production range (every 24h)
    min_barrels_24h = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('5.00'))
    max_barrels_24h = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('25.00'))
    
    # Refining capacity range (every 24h)
    min_refined_24h = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('10.00'))
    max_refined_24h = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('15.00'))
    
    is_active = models.BooleanField(default=True)
    
    # Refining settings
    refining_cooldown_hours = models.PositiveIntegerField(default=360, help_text="Default 15 days (360h)")
    refined_mineral = models.ForeignKey('game.Mineral', on_delete=models.SET_NULL, null=True, blank=True)
    refined_mineral_qty = models.PositiveIntegerField(default=1, help_text="Amount of mineral given after refining")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class UserOilCentral(models.Model):
    owner = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name="oil_centrals")
    central_type = models.ForeignKey(OilCentralType, on_delete=models.PROTECT)
    
    # These will be set upon purchase/acquisition based on the ranges in OilCentralType
    initial_life_days = models.PositiveIntegerField(default=10)
    remaining_life_days = models.IntegerField()
    barrels_24h = models.DecimalField(max_digits=10, decimal_places=2)
    refined_24h = models.DecimalField(max_digits=10, decimal_places=2)
    
    obtained_at = models.DateTimeField(auto_now_add=True)
    last_collection = models.DateTimeField(auto_now_add=True)
    
    # Refining state
    refining_charges = models.PositiveIntegerField(default=3)
    refining_start_time = models.DateTimeField(null=True, blank=True)
    refining_status = models.CharField(max_length=20, default='idle', choices=[
        ('idle', 'Inactivo'),
        ('refining', 'Refinando'),
        ('ready', 'Listo para reclamar')
    ])

    @property
    def get_life_percentage(self):
        if self.initial_life_days <= 0:
            return 0
        perc = (self.remaining_life_days / self.initial_life_days) * 100
        return max(0, min(100, perc))

    @property
    def is_claim_ready(self):
        from django.utils import timezone
        from datetime import timedelta
        if self.remaining_life_days <= 0:
            return False
        return timezone.now() >= (self.last_collection + timedelta(hours=24))

    @property
    def claim_countdown(self):
        """Returns the time remaining in seconds until the next claim, or 0 if ready."""
        from django.utils import timezone
        from datetime import timedelta
        next_claim = self.last_collection + timedelta(hours=24)
        remaining = (next_claim - timezone.now()).total_seconds()
        return max(0, int(remaining))

    @property
    def refine_countdown(self):
        """Returns seconds remaining for refining to complete."""
        from django.utils import timezone
        from datetime import timedelta
        if self.refining_status != 'refining' or not self.refining_start_time:
            return 0
        cooldown = self.central_type.refining_cooldown_hours
        finish_time = self.refining_start_time + timedelta(hours=cooldown)
        remaining = (finish_time - timezone.now()).total_seconds()
        return max(0, int(remaining))
