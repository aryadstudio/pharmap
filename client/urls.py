from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views


app_name = "patient"

urlpatterns = [
    # ── Profil patient ──
    path("profile/",             views.profile,                name="profile"),
    path("profile/edit/",        views.profile_edit,           name="profile_edit"),
    path("profile/password/",    views.profile_change_password, name="profile_password"),
    path("profile/orders/",      views.profile_orders,         name="profile_orders"),

     # ── Panier ──
    path("cart/",                views.cart_view,              name="cart"),
    path("cart/add/",            views.cart_add,               name="cart_add"),
    path("cart/update/<uuid:item_id>/", views.cart_update,     name="cart_update"),
    path("cart/clear/",          views.cart_clear,             name="cart_clear"),
]
 
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
