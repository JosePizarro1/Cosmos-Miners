from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class ChestCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Categoría de Cofre"
        verbose_name_plural = "Categorías de Cofres"

    def __str__(self):
        return self.name

class Chest(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to="chests/", help_text="Imagen o GIF del cofre")
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], help_text="Precio en Cosmos Gold (si no hay mineral seleccionado)")
    
    purchase_mineral = models.ForeignKey('game.Mineral', on_delete=models.SET_NULL, null=True, blank=True, help_text="Si se selecciona un mineral, este cofre se comprará con ese mineral en lugar de Cosmos Gold.")
    purchase_mineral_qty = models.PositiveIntegerField(default=0, help_text="Cantidad de mineral extra necesario.")
    
    is_in_store = models.BooleanField(default=True, verbose_name="¿Aparece en tienda?")
    is_black_market = models.BooleanField(default=False, verbose_name="¿Aparece en Mercado Negro?")
    black_market_discount = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Descuento en % (0-100) para el Mercado Negro")
    category = models.ForeignKey(ChestCategory, on_delete=models.SET_NULL, null=True, related_name="chests")
    
    rewards_per_open = models.PositiveIntegerField(default=1, help_text="Número de recompensas por cada apertura de cofre")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cofre"
        verbose_name_plural = "Cofres"

    def __str__(self):
        return self.name

class ChestReward(models.Model):
    chest = models.ForeignKey(Chest, on_delete=models.CASCADE, related_name="rewards")
    
    # Possible reward types (re-using existing models from models.py will be handled via imports)
    miner_reward = models.ForeignKey('game.MinerType', on_delete=models.SET_NULL, null=True, blank=True, related_name="chest_rewards")
    transport_reward = models.ForeignKey('game.TransportType', on_delete=models.SET_NULL, null=True, blank=True, related_name="chest_rewards")
    tool_reward = models.ForeignKey('game.ToolType', on_delete=models.SET_NULL, null=True, blank=True, related_name="chest_rewards")

    display_probability = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name="Probabilidad Usuario (%)",
        help_text="Lo que se muestra al usuario (ej: 10.50)"
    )
    code_probability = models.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        verbose_name="Probabilidad Código",
        help_text="Valor decimal real (ej: 0.1050). La suma de esto en un cofre debe ser 1."
    )

    class Meta:
        verbose_name = "Recompensa de Cofre"
        verbose_name_plural = "Recompensas de Cofres"

    def __str__(self):
        item_name = "Sin asignar"
        if self.miner_reward: item_name = f"Miner: {self.miner_reward.name}"
        elif self.transport_reward: item_name = f"Transport: {self.transport_reward.name}"
        elif self.tool_reward: item_name = f"Tool: {self.tool_reward.name}"
        return f"{item_name} en {self.chest.name}"

    @property
    def item_name(self):
        if self.miner_reward: return self.miner_reward.name
        if self.transport_reward: return self.transport_reward.name
        if self.tool_reward: return self.tool_reward.name
        return "Desconocido"

class UserChest(models.Model):
    owner = models.ForeignKey('game.Profile', on_delete=models.CASCADE, related_name="inventory_chests")
    chest = models.ForeignKey(Chest, on_delete=models.CASCADE)
    obtained_at = models.DateTimeField(auto_now_add=True)
    opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Cofre de Usuario"
        verbose_name_plural = "Cofres de Usuarios"

    def __str__(self):
        return f"{self.chest.name} (ID: {self.id}) de {self.owner.user.username}"
