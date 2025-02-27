from django.urls import path, include
from rest_framework import routers

from core.views import RetrieveProfileView, PostListView

router = routers.DefaultRouter()
router.register(r'posts', PostListView)
router.register(
    r'profile/followers-following',
    UserFollowersFollowingViewSet,
    basename="user_followers_following",
)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "profile/<int:id>/",
        RetrieveProfileView.as_view(),
        name="profile-retrieve"),
]

app_name = 'core'
