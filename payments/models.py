import uuid
from django.db import models
from django.conf import settings

# ==============================================================================
# MODÈLE PAIEMENT
# ==============================================================================

class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    METHOD_CHOICES = (
        ("AIRTEL", "Airtel Money"),
        ("MOOV",   "Moov Money"),
        ("CARD",   "Carte Bancaire (Stripe)"),
        ("CASH",   "Espèces (À la livraison/caisse)"),
    )

    STATUS_CHOICES = (
        ("PENDING",   "En attente"),
        ("PROCESSING","En traitement"), # Utile pour les appels API asynchrones
        ("SUCCESS",   "Payé / Succès"),
        ("FAILED",    "Échoué"),
        ("CANCELLED", "Annulé"),
        ("REFUNDED",  "Remboursé"),
    )

    # Liaison avec la commande (assurez-vous que 'orders.Order' existe bien)
    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payment"
    )

    method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        help_text="Méthode de paiement choisie par l'utilisateur."
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Montant total de la transaction."
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        db_index=True
    )

    # Identifiant de transaction externe (Stripe ID, Transaction ID Airtel/Moov)
    transaction_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="ID de transaction fourni par le prestataire (Stripe, Airtel, Moov)."
    )

    # Champs spécifiques pour le suivi
    paid_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date effective du paiement."
    )

    # Pour stocker des métadonnées JSON (réponse brute API, erreur, etc.)
    metadata = models.JSONField(
        blank=True, 
        null=True, 
        help_text="Données brutes de la réponse API (Airtel, Moov, Stripe)."
    )

    # Spécifique pour le CASH : suivi de la remise des fonds
    cash_verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_cash_payments",
        help_text="Pharmacien ayant confirmé la réception du cash."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __str__(self):
        return f"Paiement {self.get_method_display()} - {self.amount} FCFA ({self.status})"

    def is_success(self):
        return self.status == "SUCCESS"

    def is_pending(self):
        return self.status in ["PENDING", "PROCESSING"]