from django.db import models
from django.conf import settings
from decimal import Decimal

class Mineral(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="minerals/", null=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Planet(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="planets/", null=True, blank=True)
    travel_time_base = models.PositiveIntegerField(help_text="Tiempo base en horas")
    success_rate_base = models.PositiveIntegerField(help_text="Porcentaje de éxito base (%)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class PlanetMineral(models.Model):
    planet = models.ForeignKey(Planet, on_delete=models.CASCADE, related_name="produced_minerals")
    mineral = models.ForeignKey(Mineral, on_delete=models.CASCADE)
    min_amount = models.PositiveIntegerField()
    max_amount = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.mineral.name} en {self.planet.name}"

class UserMineral(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inventory_minerals")
    mineral = models.ForeignKey(Mineral, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'mineral')

    def __str__(self):
        return f"{self.user.username} - {self.mineral.name}: {self.amount}"

class MiningTrip(models.Model):
    STATUS_CHOICES = [
        ('ongoing', 'En viaje'),
        ('finished', 'Terminado'),
        ('collected', 'Recolectado'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    planet = models.ForeignKey(Planet, on_delete=models.CASCADE)
    
    # Assets used (using string references to avoid circular imports if imported in models.py)
    miner = models.ForeignKey('game.UserMiner', on_delete=models.PROTECT)
    tool = models.ForeignKey('game.UserTool', on_delete=models.PROTECT)
    transport = models.ForeignKey('game.UserTransport', on_delete=models.PROTECT)
    
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()
    
    # Snapshot of stats at start of trip
    attempts = models.PositiveIntegerField()
    success_rate = models.PositiveIntegerField()
    production_multiplier = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Results stored as JSON to be claimed later
    # Format: {"gold": 10, "mineral_alien": 5}
    results_json = models.JSONField(default=dict, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')

    def __eventually_calculate_results(self):
        # This will be called when the trip transitions from ongoing to finished
        pass

    @property
    def total_hours(self):
        """Duración total del viaje en horas."""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            hours = delta.total_seconds() / 3600
            return round(hours, 1)
        return 0

    def __str__(self):
        return f"Viaje de {self.user.username} a {self.planet.name} ({self.status})"
