from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Alliance(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=500, blank=True)
    image = models.ImageField(upload_to="alliances/", null=True, blank=True)
    
    leader = models.ForeignKey(User, on_delete=models.CASCADE, related_name="led_alliance")
    right_hand = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="secondary_led_alliance")
    captain = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="captain_of_alliance")
    
    max_members = models.PositiveIntegerField(default=10)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class AllianceRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptada'),
        ('rejected', 'Rechazada'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="alliance_requests")
    alliance = models.ForeignKey(Alliance, on_delete=models.CASCADE, related_name="requests")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'alliance')

    def __str__(self):
        return f"{self.user.username} -> {self.alliance.name} ({self.status})"

class AllianceGlobalConfig(models.Model):
    default_max_members = models.PositiveIntegerField(default=10)
    
    def __str__(self):
        return "Configuración Global de Alianzas"
    
    @classmethod
    def get_config(cls):
        config, created = cls.objects.get_or_create(id=1)
        return config

class AlliancePlanet(models.Model):
    alliance = models.ForeignKey(Alliance, on_delete=models.CASCADE, related_name="owned_planets")
    planet = models.ForeignKey('game.Planet', on_delete=models.CASCADE)
    acquired_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('alliance', 'planet')

    def __str__(self):
        return f"{self.alliance.name} posee {self.planet.name}"

