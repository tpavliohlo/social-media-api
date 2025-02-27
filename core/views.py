from django.db.models import Count
from django.shortcuts import render
from rest_framework import generics, viewsets, views, status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Profile, Post, Like
from core.permissions import IsOwnerOrReadOnly
from core.serializers import RetrieveProfileSerializer, PostSerializer, PostRetrieveSerializer, LikesListPostSerializer, \
    LikeCreatePostSerializer


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

    def retrieve(self, request, *args, **kwargs):
        print("Requested by user:", request.user)
        return super().retrieve(request, *args, **kwargs)


class LikesView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        post_id = get_object_or_404(Post, pk=pk)
        likes = Like.objects.filter(post=post_id)
        serializer = LikesListPostSerializer(likes, many=True)
        return Response(serializer.data)

    def post(self, request, pk, *args, **kwargs):
        post_id = get_object_or_404(Post, pk=pk)
        existing_like = Like.objects.filter(
            post=post_id,
            user=request.user
        ).first()
        if existing_like:
            return Response(
                {"detail": "You have already liked this post."},
                status=status.HTTP_400_BAD_REQUEST
            )
        like = Like.objects.create(post=post_id, user=request.user)
        serializer = LikeCreatePostSerializer(like)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk, *args, **kwargs):
        self.permission_classes = [IsOwnerOrReadOnly]
        post_id = get_object_or_404(Post, pk=pk)
        existing_like = Like.objects.filter(
            post=post_id,
            user=request.user
        ).first()
        if not existing_like:
            return Response(
                {"detail": "You have not already liked this post."},
                status=status.HTTP_400_BAD_REQUEST
            )
        existing_like.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
