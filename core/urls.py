from django.urls import path

from core.views import RetrieveProfileView

urlpatterns = [
    path("profile/<int:id>/", RetrieveProfileView.as_view(), name="profile-retrieve"),
]

app_name = 'core'