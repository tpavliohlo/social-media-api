from rest_framework import permissions

from core.models import Blocked, Follower, Profile


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners of an object to edit it."""
    def has_object_permission(self, request, view, obj):
    # Read permissions are allowed for any request, so we always allow GET, HEAD, or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the post.
        return obj.owner == request.user


class CanViewPostPermission(permissions.BasePermission):
    """
    Permission to check if a post can be viewed or not.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        post = view.get_object()

        if Blocked.objects.filter(blocker=request.user, blocked=post.owner).exists():
            return False

        if post.owner.profile.privacy_settings == Profile.PrivacySettings.PRIVATE:
            if not post.owner in Follower.objects.filter(
                follower=request.user
            ).values_list("following", flat=True):
                return False

        return True


class CanLikePostPermission(permissions.BasePermission):
    """
    Permission to check if a post can be liked or not.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        post = view.get_object()

        if Blocked.objects.filter(blocker=request.user, blocked=post.owner).exists():
            return False

        if post.owner.profile.privacy_settings == Profile.PrivacySettings.PRIVATE:
            if not post.owner in Follower.objects.filter(
                follower=request.user
            ).values_list("following", flat=True):
                return False

        return True


class CanCommentOnPostPermission(permissions.BasePermission):
    """
    Permission to check if a post can be commented or not.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        post = view.get_object()

        if Blocked.objects.filter(blocker=request.user, blocked=post.owner).exists():
            return False

        if post.owner.profile.privacy_settings == Profile.PrivacySettings.PRIVATE:
            if not post.owner in Follower.objects.filter(
                follower=request.user
            ).values_list("following", flat=True):
                return False

        return True
