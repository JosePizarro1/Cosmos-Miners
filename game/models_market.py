from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone

class MarketConfig(models.Model):
    """
    Configuración de intercambio para un mineral específico.
    """
    mineral = models.ForeignKey('game.Mineral', on_delete=models.CASCADE, related_name='market_configs')
    is_black = models.BooleanField(default=False, help_text="¿Pertenece al mercado Black / BlackGOLD?")
    gold_multiplier = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        help_text="Relación: 1 unidad de mineral = X Gold (Cosmos o Black)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        tipo = "Black" if self.is_black else "Standard"
        return f"({tipo}) {self.mineral.name} x{self.gold_multiplier}"

class MarketGlobalSettings(models.Model):
    """
    Configuraciones globales del mercado.
    """
    standard_cooldown_hours = models.PositiveIntegerField(default=864, help_text="Cooldown estándar (ej: 36 días = 864h)")
    black_cooldown_hours = models.PositiveIntegerField(default=864, help_text="Cooldown mercado black")
    
    last_updated = models.DateTimeField(auto_now=True)

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj

class UserMarketStatus(models.Model):
    """
    Estado de cooldown del mercado para cada usuario.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='market_status')
    
    standard_cooldown_until = models.DateTimeField(null=True, blank=True)
    black_cooldown_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Market Status: {self.user.username}"

class UserMarketExchange(models.Model):
    """
    Registro de un intercambio activo o finalizado de un usuario.
    Similar a UserActiveTrade pero con cantidades dinámicas.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='market_exchanges')
    mineral = models.ForeignKey('game.Mineral', on_delete=models.CASCADE)
    amount_mineral = models.PositiveIntegerField()
    gold_expected = models.DecimalField(max_digits=12, decimal_places=2)
    
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()
    
    is_claimed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Reclamado" if self.is_claimed else "En Proceso"
        return f"Intercambio {self.user.username}: {self.amount_mineral} {self.mineral.name} ({status})"
