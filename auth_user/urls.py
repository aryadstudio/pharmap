from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = "auth_user"

urlpatterns = [
    path("register/",            views.register_patient,    name="register"),
    path("register/pharmacist/", views.register_pharmacist, name="register_pharmacist"),
    path("login/",               views.login_patient,       name="login"),
    path("login/pharmacist/",    views.login_pharmacist,    name="login_pharmacist"),
    path("logout/",              views.logout_view,         name="logout"),
    path("profile/",             views.profile_view,        name="profile"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
