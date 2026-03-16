from django.db import models
from django.utils import timezone

class Season(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nombre de la Temporada")
    start_date = models.DateTimeField(verbose_name="Fecha de Inicio")
    end_date = models.DateTimeField(verbose_name="Fecha de Fin")
    claim_rewards_at = models.DateTimeField(verbose_name="Fecha para Reclamar Recompensas")
    is_active_override = models.BooleanField(default=False, verbose_name="Forzar como Temporada Actual")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = "Temporada"
        verbose_name_plural = "Temporadas"

    def __str__(self):
        return self.name

    @property
    def status(self):
        now = timezone.now()
        if self.is_active_override:
            return "active"
        if now < self.start_date:
            return "upcoming"
        if self.start_date <= now <= self.end_date:
            return "active"
        return "finished"

    @property
    def time_until_start(self):
        now = timezone.now()
        if now < self.start_date:
            return self.start_date - now
        return None

class SeasonLevel(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="levels")
    name = models.CharField(max_length=100, verbose_name="Nombre del Nivel")
    lock_duration_days = models.PositiveIntegerField(default=7, verbose_name="Días de Inhabilitación de items")
    
    class Meta:
        ordering = ['name']
        verbose_name = "Nivel de Temporada"
        verbose_name_plural = "Niveles de Temporada"

    def __str__(self):
        return f"{self.season.name} - {self.name}"

class SeasonLevelRequirement(models.Model):
    TYPE_CHOICES = [
        ('miner_attempts', 'Mín. Intentos Minero'),
        ('transport_speed', 'Mín. Velocidad (Transporte)'),
        ('tool_multiplier', 'Mín. Multiplicador (Herramienta)'),
    ]
    level = models.ForeignKey(SeasonLevel, on_delete=models.CASCADE, related_name="requirements")
    requirement_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.level.name} - {self.get_requirement_type_display()}: {self.value}"

class UserSeasonEntry(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    level = models.ForeignKey(SeasonLevel, on_delete=models.CASCADE)
    
    miner_used = models.ForeignKey('game.UserMiner', on_delete=models.SET_NULL, null=True, blank=True)
    transport_used = models.ForeignKey('game.UserTransport', on_delete=models.SET_NULL, null=True, blank=True)
    tool_used = models.ForeignKey('game.UserTool', on_delete=models.SET_NULL, null=True, blank=True)
    
    entered_at = models.DateTimeField(auto_now_add=True)
    locked_until = models.DateTimeField()

    class Meta:
        unique_together = ('user', 'season')
        verbose_name = "Entrada a Temporada"
        verbose_name_plural = "Entradas a Temporada"
