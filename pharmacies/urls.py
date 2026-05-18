from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'pharmacies'

urlpatterns = [
    path('', views.pharmacy_list, name='pharmacy_list'),
    path('search/', views.pharmacy_search, name='search'),
    path('<str:pharmacy_id>/', views.pharmacy_detail, name='pharmacy_detail'),
    path('<str:pharmacy_id>/reviews/', views.pharmacy_reviews, name='pharmacy_reviews'),
    path('autocomplete/', views.autocomplete, name='autocomplete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
