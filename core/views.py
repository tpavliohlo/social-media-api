from django.db.models import Count
from django.shortcuts import render
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated

from core.models import Profile, Post
from core.permissions import IsOwnerOrReadOnly
from core.serializers import RetrieveProfileSerializer, PostSerializer, PostRetrieveSerializer


class RetrieveProfileView(generics.RetrieveAPIView):
    queryset = Profile.objects.all()
    serializer_class = RetrieveProfileSerializer
    lookup_field = 'id'

    def get_queryset(self):
        queryset = self.queryset
        return queryset.annotate(
            following=Count("user__following", distinct=True),
            followers=Count("user__followers", distinct=True),
        )


class PostListView(viewsets.ModelViewSet):
    queryset = Post.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return PostSerializer
        return PostRetrieveSerializer

    def get_permissions(self):
        if self.action in ("retrieve", "create"):
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsOwnerOrReadOnly]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
