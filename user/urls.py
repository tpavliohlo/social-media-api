from django.urls import path, include
from rest_framework.authtoken import views

from rest_framework.routers import DefaultRouter

from user.views import UserCreateView, LoginUserView, ManageUserView, LogoutView

router = DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
    path("register/", UserCreateView.as_view(), name="register"),
    path("login/", LoginUserView.as_view(), name="login"),
    path("me/", ManageUserView.as_view(), name="manage"),
    path("logout/", LogoutView.as_view(), name="logout"),
]

app_name = 'user'
