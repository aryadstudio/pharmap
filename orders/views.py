from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from .models import Order, OrderItem
from .forms import OrderStatusForm, OrderItemFormSet
from medications.models import PharmacyMedication
from pharmacies.models import Pharmacy


@login_required
def order_list(request):
    """Liste des commandes du patient connecté (ou toutes si pharmacien)."""
    user = request.user

    if user.role == "PHARMACIST":
        orders = Order.objects.filter(
            pharmacy=user.pharmacy
        ).select_related("patient", "pharmacy").prefetch_related("items")
    else:
        orders = Order.objects.filter(
            patient=user
        ).select_related("pharmacy").prefetch_related("items")

    context = {
        "orders":       orders,
        "status_list":  Order.STATUS_CHOICES,
        "active_filter": request.GET.get("status", ""),
    }

    if context["active_filter"]:
        orders = orders.filter(status=context["active_filter"])
        context["orders"] = orders

    return render(request, "orders/order_list.html", context)


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("patient", "pharmacy")
                     .prefetch_related("items__medication", "payment"),
        id=order_id
    )

    # Seul le patient ou le pharmacien propriétaire peut voir la commande
    if request.user != order.patient and getattr(request.user, "pharmacy", None) != order.pharmacy:
        messages.error(request, "Accès non autorisé.")
        return redirect("orders:order_list")

    return render(request, "orders/order_detail.html", {"order": order})


@login_required
def order_create(request, pharmacy_id):
    pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id, is_verified=True)

    if request.user.role != "PATIENT":
        messages.error(request, "Seuls les patients peuvent passer une commande.")
        return redirect("pharmacies:pharmacy_detail", pharmacy_id=pharmacy_id)

    # Stocks disponibles dans cette pharmacie
    stocks = PharmacyMedication.objects.filter(
        pharmacy=pharmacy, is_available=True, quantity__gt=0
    ).select_related("medication")

    if request.method == "POST":
        formset = OrderItemFormSet(request.POST)

        if formset.is_valid():
            items_data = [f.cleaned_data for f in formset if f.cleaned_data and not f.cleaned_data.get("DELETE")]

            if not items_data:
                messages.error(request, "Ajoutez au moins un médicament.")
                return render(request, "orders/order_create.html", {"formset": formset, "pharmacy": pharmacy, "stocks": stocks})

            with transaction.atomic():
                total = 0
                order = Order.objects.create(
                    patient=request.user,
                    pharmacy=pharmacy,
                    status="PENDING",
                    total_amount=0,
                    note=request.POST.get("note", ""),
                )

                for item in items_data:
                    medication = item["medication"]
                    quantity   = item["quantity"]

                    stock = stocks.filter(medication=medication).first()
                    if not stock:
                        messages.error(request, f"{medication.name} n'est pas disponible dans cette pharmacie.")
                        order.delete()
                        return redirect("orders:order_create", pharmacy_id=pharmacy_id)

                    if stock.quantity < quantity:
                        messages.error(request, f"Stock insuffisant pour {medication.name} (disponible : {stock.quantity}).")
                        order.delete()
                        return redirect("orders:order_create", pharmacy_id=pharmacy_id)

                    subtotal = stock.price * quantity
                    total   += subtotal

                    OrderItem.objects.create(
                        order=order,
                        medication=medication,
                        quantity=quantity,
                        unit_price=stock.price,
                        subtotal=subtotal,
                    )

                order.total_amount = total
                order.save(update_fields=["total_amount"])

            messages.success(request, "Votre commande a bien été envoyée !")
            return redirect("orders:order_detail", order_id=order.id)

    else:
        formset = OrderItemFormSet()

    return render(request, "orders/order_create.html", {
        "formset":  formset,
        "pharmacy": pharmacy,
        "stocks":   stocks,
    })


@login_required
def order_cancel(request, order_id):
    order = get_object_or_404(Order, id=order_id, patient=request.user)

    if not order.is_cancellable():
        messages.error(request, "Cette commande ne peut plus être annulée.")
        return redirect("orders:order_detail", order_id=order_id)

    if request.method == "POST":
        order.status = "CANCELLED"
        order.save(update_fields=["status"])
        messages.success(request, "Commande annulée.")
        return redirect("orders:order_list")

    return render(request, "orders/order_confirm_cancel.html", {"order": order})


@login_required
def order_status_update(request, order_id):
    """Réservé au pharmacien propriétaire."""
    order = get_object_or_404(Order, id=order_id)

    if getattr(request.user, "pharmacy", None) != order.pharmacy:
        messages.error(request, "Accès non autorisé.")
        return redirect("orders:order_list")

    if request.method == "POST":
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f"Statut mis à jour : {order.get_status_display()}")
            return redirect("orders:order_detail", order_id=order_id)
    else:
        form = OrderStatusForm(instance=order)

    return render(request, "orders/order_status_update.html", {"form": form, "order": order})