from django.urls import path, include
from rest_framework import routers

from core.views import RetrieveProfileView, PostListView

router = routers.DefaultRouter()
router.register(r'posts', PostListView)

urlpatterns = [
    path("", include(router.urls)),
    path("profile/<int:id>/", RetrieveProfileView.as_view(), name="profile-retrieve"),
]

app_name = 'core'
