from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("user/", include("auth_user.urls")),
    path("pharmacies/", include("pharmacies.urls")),
    path("medications/", include("medications.urls")),
    path("orders/", include("orders.urls")),
    path("chats/", include("chats.urls")),
    path("client/", include("client.urls"), name="client"),
    path("",views.home, name="home"),
    path("how-it-works/", views.how_it_works, name="how_it_works"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
