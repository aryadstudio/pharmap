from django.db import models
from django.core.validators import MinValueValidator
import uuid


class Cart(models.Model):
    """
    Panier d'un client (patient)
    Un panier est unique par utilisateur et contient des articles temporaires
    avant la validation de la commande.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    patient = models.OneToOneField(
        "auth_user.User",
        on_delete=models.CASCADE,
        related_name="cart",
        limit_choices_to={'role': 'PATIENT'}
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Panier"
        verbose_name_plural = "Paniers"
    
    def __str__(self):
        return f"Panier de {self.patient.username}"
    
    def get_total_amount(self):
        """Calcule le montant total du panier"""
        total = self.items.aggregate(total=models.Sum('subtotal'))['total']
        return total or 0
    
    def get_item_count(self):
        """Retourne le nombre total d'articles dans le panier"""
        return self.items.aggregate(count=models.Sum('quantity'))['count'] or 0
    
    def is_empty(self):
        """Vérifie si le panier est vide"""
        return not self.items.exists()
    
    def clear(self):
        """Vide le panier"""
        self.items.all().delete()


class CartItem(models.Model):
    """
    Article dans le panier d'un client
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )
    
    medication = models.ForeignKey(
        "medications.Medication",
        on_delete=models.CASCADE
    )
    
    pharmacy = models.ForeignKey(
        "pharmacies.Pharmacy",
        on_delete=models.CASCADE,
        help_text="Pharmacie où le médicament est disponible"
    )
    
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        default=1
    )
    
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Prix au moment de l'ajout au panier"
    )
    
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        editable=False
    )
    
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Article du panier"
        verbose_name_plural = "Articles du panier"
        unique_together = ("cart", "medication", "pharmacy")
        ordering = ("-added_at",)
    
    def __str__(self):
        return f"{self.quantity}× {self.medication.name} (panier de {self.cart.patient.username})"
    
    def save(self, *args, **kwargs):
        """Calcule automatiquement le sous-total"""
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)