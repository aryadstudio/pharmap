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
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
