from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import PermissionDenied

from .models import Order, OrderItem
from .forms import OrderStatusForm, OrderItemFormSet
from medications.models import PharmacyMedication
from pharmacies.models import Pharmacy


@login_required
def order_list(request):
    """Liste des commandes du patient connecté ou de la pharmacie."""
    user = request.user

    if user.role == "PHARMACIST":
        try:
            pharmacy = user.pharmacy
            orders = Order.objects.filter(
                pharmacy=pharmacy
            ).select_related("patient", "pharmacy").prefetch_related("items", "payment")
        except Pharmacy.DoesNotExist:
            messages.error(request, "Aucune pharmacie associée à votre compte.")
            return redirect("home")
    else:
        orders = Order.objects.filter(
            patient=user
        ).select_related("pharmacy").prefetch_related("items", "payment")

    # Filtrage par statut si demandé
    status_filter = request.GET.get("status", "")
    if status_filter:
        orders = orders.filter(status=status_filter)

    context = {
        "orders": orders,
        "status_list": Order.STATUS_CHOICES,
        "active_filter": status_filter,
    }
    return render(request, "orders/order_list.html", context)


@login_required
def order_detail(request, order_id):
    """Détail d'une commande."""
    order = get_object_or_404(
        Order.objects.select_related("patient", "pharmacy")
                     .prefetch_related("items__medication", "payment"),
        id=order_id
    )

    # Vérification des permissions
    is_patient = request.user == order.patient
    is_pharmacist = getattr(request.user, "pharmacy", None) == order.pharmacy
    is_admin = request.user.role == "ADMIN"

    if not (is_patient or is_pharmacist or is_admin):
        raise PermissionDenied("Accès non autorisé à cette commande.")

    context = {
        "order": order,
        "is_patient": is_patient,
        "is_pharmacist": is_pharmacist,
    }
    return render(request, "orders/order_detail.html", context)


@login_required
def order_create(request, pharmacy_id):
    """Création d'une nouvelle commande pour une pharmacie donnée."""
    pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id, is_verified=True)

    if request.user.role != "PATIENT":
        messages.error(request, "Seuls les patients peuvent passer une commande.")
        return redirect("pharmacies:pharmacy_detail", pharmacy_id=pharmacy_id)

    # Récupération des stocks disponibles
    stocks = PharmacyMedication.objects.filter(
        pharmacy=pharmacy, 
        is_available=True, 
        quantity__gt=0
    ).select_related("medication").order_by("medication__name")

    if request.method == "POST":
        formset = OrderItemFormSet(request.POST)

        if formset.is_valid():
            items_data = []
            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get("DELETE"):
                    # Ignorer les lignes vides
                    if form.cleaned_data.get("medication") and form.cleaned_data.get("quantity"):
                        items_data.append(form.cleaned_data)

            if not items_data:
                messages.error(request, "Veuillez ajouter au moins un médicament à la commande.")
                return render(request, "orders/order_create.html", {
                    "formset": formset, 
                    "pharmacy": pharmacy, 
                    "stocks": stocks
                })

            try:
                with transaction.atomic():
                    # Création de la commande vide
                    order = Order.objects.create(
                        patient=request.user,
                        pharmacy=pharmacy,
                        status="PENDING",
                        total_amount=0, # Sera mis à jour juste après
                        note=request.POST.get("note", ""),
                    )

                    total_amount = 0
                    errors = []

                    for item in items_data:
                        medication = item["medication"]
                        quantity = item["quantity"]

                        # Vérification du stock spécifique à cette pharmacie
                        try:
                            stock = stocks.get(medication=medication)
                        except PharmacyMedication.DoesNotExist:
                            errors.append(f"{medication.name} n'est plus disponible.")
                            continue

                        if stock.quantity < quantity:
                            errors.append(f"Stock insuffisant pour {medication.name} (disponible: {stock.quantity}).")
                            continue

                        unit_price = stock.price
                        subtotal = unit_price * quantity
                        total_amount += subtotal

                        OrderItem.objects.create(
                            order=order,
                            medication=medication,
                            quantity=quantity,
                            unit_price=unit_price,
                            subtotal=subtotal,
                        )

                    if errors:
                        # Si erreurs, on annule tout (rollback automatique grâce à atomic)
                        # Mais comme on est sorti du bloc avec raise ou logique manuelle, ici on gère proprement
                        raise ValueError("; ".join(errors))

                    # Mise à jour du total
                    order.total_amount = total_amount
                    order.save(update_fields=["total_amount"])

                messages.success(request, "Votre commande a été envoyée avec succès !")
                return redirect("orders:order_detail", order_id=order.id)

            except ValueError as e:
                messages.error(request, str(e))
                # Le contexte sera re-rendu avec le formset rempli
            except Exception as e:
                messages.error(request, "Une erreur technique est survenue. Veuillez réessayer.")
        
        # Si le formset n'est pas valide ou erreur, on recharge la page avec les erreurs
        return render(request, "orders/order_create.html", {
            "formset": formset, 
            "pharmacy": pharmacy, 
            "stocks": stocks
        })

    else:
        formset = OrderItemFormSet()

    return render(request, "orders/order_create.html", {
        "formset": formset,
        "pharmacy": pharmacy,
        "stocks": stocks,
    })


@login_required
def order_cancel(request, order_id):
    """Annulation d'une commande par le patient."""
    order = get_object_or_404(Order, id=order_id, patient=request.user)

    if not order.is_cancellable():
        messages.error(request, "Cette commande ne peut plus être annulée car elle est déjà en cours de traitement ou livrée.")
        return redirect("orders:order_detail", order_id=order_id)

    if request.method == "POST":
        order.status = "CANCELLED"
        order.save(update_fields=["status"])
        messages.success(request, "La commande a été annulée.")
        return redirect("orders:order_list")

    return render(request, "orders/order_confirm_cancel.html", {"order": order})


@login_required
def order_status_update(request, order_id):
    """Mise à jour du statut par le pharmacien."""
    order = get_object_or_404(Order, id=order_id)

    # Vérification que c'est bien le pharmacien propriétaire
    user_pharmacy = getattr(request.user, "pharmacy", None)
    if not user_pharmacy or user_pharmacy != order.pharmacy:
        messages.error(request, "Accès non autorisé.")
        return redirect("orders:order_list")

    if request.method == "POST":
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f"Le statut de la commande a été mis à jour : {order.get_status_display()}")
            return redirect("orders:order_detail", order_id=order_id)
    else:
        form = OrderStatusForm(instance=order)

    return render(request, "orders/order_status_update.html", {"form": form, "order": order})