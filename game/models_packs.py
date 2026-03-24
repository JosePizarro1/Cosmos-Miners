from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class StorePack(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nombre del Paquete")
    description = models.TextField(verbose_name="Descripción")
    image = models.ImageField(upload_to="packs/", null=True, blank=True, verbose_name="Imagen")

    # Precio en Cosmos Gold
    price_gold = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Precio en GOLD"
    )

    # Mineral alternativo de pago
    purchase_mineral = models.ForeignKey(
        'game.Mineral',
        on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Mineral de compra alternativo"
    )
    purchase_mineral_qty = models.IntegerField(
        default=0,
        verbose_name="Cantidad de mineral requerida"
    )

    # Link externo (prioridad absoluta sobre precio)
    external_link = models.URLField(
        max_length=500, null=True, blank=True,
        verbose_name="Link Externo",
        help_text="Si se llena, el botón de compra abrirá este enlace. No se cobrará GOLD ni mineral."
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Paquete"
        verbose_name_plural = "Paquetes"

    def __str__(self):
        return f"Pack: {self.name}"


class PackMinerReward(models.Model):
    """Un minero elegible dentro de un paquete con su probabilidad."""
    pack = models.ForeignKey(StorePack, on_delete=models.CASCADE, related_name="miner_rewards")
    miner = models.ForeignKey(
        'game.MinerType', on_delete=models.CASCADE,
        verbose_name="Tipo de Minero"
    )
    # Probabilidad real usada por el algoritmo de sorteo
    chance = models.DecimalField(
        max_digits=6, decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Probabilidad real entre 0 y 1 (ej: 0.15 = 15%). La suma del pack debe ser 1."
    )
    # Texto visible para el usuario en la UI
    probability_label = models.CharField(
        max_length=50,
        help_text="Texto visible para el usuario. Ej: 'Alta', '15%', 'Muy Rara'"
    )

    def __str__(self):
        return f"{self.pack.name} | Minero: {self.miner.name} ({self.chance})"


class PackToolReward(models.Model):
    """Una herramienta elegible dentro de un paquete con su probabilidad."""
    pack = models.ForeignKey(StorePack, on_delete=models.CASCADE, related_name="tool_rewards")
    tool = models.ForeignKey(
        'game.ToolType', on_delete=models.CASCADE,
        verbose_name="Tipo de Herramienta"
    )
    chance = models.DecimalField(
        max_digits=6, decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Probabilidad real entre 0 y 1. La suma del pack debe ser 1."
    )
    probability_label = models.CharField(
        max_length=50,
        help_text="Texto visible para el usuario. Ej: 'Común', '30%'"
    )

    def __str__(self):
        return f"{self.pack.name} | Herramienta: {self.tool.name} ({self.chance})"


class PackTransportReward(models.Model):
    """Un transporte elegible dentro de un paquete con su probabilidad."""
    pack = models.ForeignKey(StorePack, on_delete=models.CASCADE, related_name="transport_rewards")
    transport = models.ForeignKey(
        'game.TransportType', on_delete=models.CASCADE,
        verbose_name="Tipo de Transporte"
    )
    chance = models.DecimalField(
        max_digits=6, decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Probabilidad real entre 0 y 1. La suma del pack debe ser 1."
    )
    probability_label = models.CharField(
        max_length=50,
        help_text="Texto visible para el usuario. Ej: 'Épico', '5%'"
    )

    def __str__(self):
        return f"{self.pack.name} | Transporte: {self.transport.name} ({self.chance})"


class PackBlessingReward(models.Model):
    """Una bendición dinámica elegible dentro de un paquete."""
    pack = models.ForeignKey(StorePack, on_delete=models.CASCADE, related_name="blessing_rewards")
    blessing = models.ForeignKey(
        'game.Blessing', on_delete=models.CASCADE,
        verbose_name="Bendición Dinámica"
    )
    chance = models.DecimalField(
        max_digits=6, decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Probabilidad real entre 0 y 1. La suma del pack debe ser 1."
    )
    probability_label = models.CharField(
        max_length=50,
        help_text="Texto visible para el usuario. Ej: 'Gesto de Suerte', '1%'"
    )

    def __str__(self):
        return f"{self.pack.name} | Bendición: {self.blessing.name} ({self.chance})"


class PackPurchaseLog(models.Model):
    """Registro de compra de paquetes por usuario."""
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name="pack_purchases")
    pack = models.ForeignKey(StorePack, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} compró {self.pack.name} el {self.purchased_at}"
