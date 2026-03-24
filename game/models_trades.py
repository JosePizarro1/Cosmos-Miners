from django.db import models
from django.conf import settings
from decimal import Decimal

class TradeOffer(models.Model):
    mineral = models.ForeignKey('game.Mineral', on_delete=models.CASCADE, related_name='trade_offers')
    mineral_qty = models.PositiveIntegerField(help_text="Cantidad de mineral requerida")
    gold_reward = models.DecimalField(max_digits=12, decimal_places=2, help_text="Recompensa en Cosmos Gold")
    duration_hours = models.PositiveIntegerField(default=360, help_text="Duración en horas (ej: 360 para 15 días)")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.mineral_qty} {self.mineral.name} por {self.gold_reward} GOLD ({self.duration_hours}h)"

class UserActiveTrade(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='active_trades')
    offer = models.ForeignKey(TradeOffer, on_delete=models.CASCADE)
    
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()
    
    is_claimed = models.BooleanField(default=False)

    def __str__(self):
        return f"Venta de {self.user.username} - {self.offer.mineral.name} ({'Reclamado' if self.is_claimed else 'En progreso'})"
