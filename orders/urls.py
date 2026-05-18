from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
app_name = 'orders'

urlpatterns = [
    path("",                          views.order_list,    name="order_list"),
    path("create/<int:pharmacy_id>/", views.order_create,  name="order_create"),
    path("<int:order_id>/",           views.order_detail,  name="order_detail"),
    path("<int:order_id>/cancel/",    views.order_cancel,  name="order_cancel"),
    path("<int:order_id>/status/",    views.order_status_update, name="order_status_update"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
