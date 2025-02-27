from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from user.serializers import UserFollowersFollowingSerializer


class UserFollowersFollowingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserFollowersFollowingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return [user]