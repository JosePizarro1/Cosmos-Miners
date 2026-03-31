from django.db import models
from django.conf import settings
from django.utils import timezone


class AllianceGift(models.Model):
    """Template for a gift that an admin can create and later assign to alliances."""
    name = models.CharField(max_length=150)
    image = models.ImageField(upload_to="alliance_gifts/", null=True, blank=True)
    description = models.TextField(max_length=500, blank=True)

    # Contents — all optional, a gift can contain any combination
    gold_amount = models.PositiveIntegerField(default=0, help_text="Cosmos Gold a entregar")

    mineral = models.ForeignKey(
        'game.Mineral', on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Mineral a entregar"
    )
    mineral_quantity = models.PositiveIntegerField(default=0, help_text="Cantidad del mineral")

    miner_type = models.ForeignKey(
        'game.MinerType', on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Tipo de minero a entregar"
    )
    tool_type = models.ForeignKey(
        'game.ToolType', on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Tipo de herramienta a entregar"
    )
    transport_type = models.ForeignKey(
        'game.TransportType', on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Tipo de transporte a entregar"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_contents_display(self):
        """Return a list of human-readable content strings."""
        items = []
        if self.gold_amount:
            items.append(f"{self.gold_amount} Gold")
        if self.mineral and self.mineral_quantity:
            items.append(f"{self.mineral_quantity} {self.mineral.name}")
        if self.miner_type:
            items.append(f"Minero: {self.miner_type.name}")
        if self.tool_type:
            items.append(f"Herramienta: {self.tool_type.name}")
        if self.transport_type:
            items.append(f"Transporte: {self.transport_type.name}")
        return items


class AllianceGiftAssignment(models.Model):
    """Links a gift to an alliance. Consumed once raffled."""
    gift = models.ForeignKey(AllianceGift, on_delete=models.CASCADE, related_name="assignments")
    alliance = models.ForeignKey('game.Alliance', on_delete=models.CASCADE, related_name="gift_assignments")
    is_raffled = models.BooleanField(default=False)
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Sorteado" if self.is_raffled else "Disponible"
        return f"{self.gift.name} → {self.alliance.name} ({status})"


class AllianceGiftWinner(models.Model):
    """Records the winner of a raffle."""
    assignment = models.OneToOneField(AllianceGiftAssignment, on_delete=models.CASCADE, related_name="winner_record")
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gift_wins")
    won_at = models.DateTimeField(auto_now_add=True)
    is_claimed = models.BooleanField(default=False)

    def __str__(self):
        status = " (Reclamado)" if self.is_claimed else " (Pendiente)"
        return f"{self.winner.username} ganó {self.assignment.gift.name}{status}"
