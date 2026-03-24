from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User

class Blessing(models.Model):
    """Bendiciones dinámicas que se pueden crear y editar."""
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='blessings/', null=True, blank=True)
    
    # Costo: O es Gold o es Mineral, no ambos.
    price_gold = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    price_mineral = models.ForeignKey('game.Mineral', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    price_mineral_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Recompensa
    reward_mineral = models.ForeignKey('game.Mineral', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    reward_mineral_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reward_gold = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    cooldown_hours = models.PositiveIntegerField(default=24, help_text="Horas antes de poder reclamar de nuevo")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class StaticBlessing(models.Model):
    """Configuración para las 4 bendiciones fijas (Petróleo, VIP, Cosmos, y una extra)."""
    TYPE_CHOICES = [
        ('oil', 'Bendición del Petróleo'),
        ('vip', 'Bendición VIP'),
        ('cosmos', 'Bendición Cosmos'),
        ('extra', 'Bendición Extra'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, unique=True)
    name = models.CharField(max_length=100)
    bonus_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Porcentaje visual (ej: 1.00 para 1%)")
    
    # Solo para la bendición Cosmos
    required_pack = models.ForeignKey('game.StorePack', on_delete=models.SET_NULL, null=True, blank=True, help_text="Pack requerido para la bendición Cosmos")
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.name}"

class UserBlessingClaim(models.Model):
    """Registro de reclamo de bendiciones por usuario."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blessings_claims")
    
    # Puede ser una bendición dinámica o una estática
    blessing = models.ForeignKey(Blessing, on_delete=models.CASCADE, null=True, blank=True)
    static_blessing = models.ForeignKey(StaticBlessing, on_delete=models.CASCADE, null=True, blank=True)
    
    claimed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'blessing']),
            models.Index(fields=['user', 'static_blessing']),
        ]

    def __str__(self):
        target = self.blessing.name if self.blessing else self.static_blessing.name
        return f"{self.user.username} reclamó {target}"

class UserDynamicBlessing(models.Model):
    """Benciones dinámicas que el usuario ha comprado y puede farmear."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_dynamic_blessings")
    blessing = models.ForeignKey(Blessing, on_delete=models.CASCADE)
    obtained_at = models.DateTimeField(auto_now_add=True)
    last_claim_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'blessing')
        
    def __str__(self):
        return f"{self.user.username} - {self.blessing.name}"
