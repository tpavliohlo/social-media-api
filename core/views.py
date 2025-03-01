from django.db.models import Count, Value, Case, When, IntegerField
from django.shortcuts import render
from rest_framework import generics, viewsets, views, status
from rest_framework.generics import get_object_or_404, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import (
    Profile,
    Post,
    Like,
    Comment,
    Blocked,
    Follower,
)
from core.permissions import IsOwnerOrReadOnly
from core.serializers import (
    RetrieveProfileSerializer,
    PostSerializer,
    PostRetrieveSerializer,
    LikesListPostSerializer,
    LikeCreatePostSerializer,
    CommentsListPostSerializer,
    BlockedListUserSerializer,
    UserProfileSerializer,
    LikedPostSerializer,
)
from user.models import User


class RetrieveProfileView(generics.RetrieveAPIView):
    queryset = Profile.objects.all()
    serializer_class = RetrieveProfileSerializer
    lookup_field = 'id'

    def get_queryset(self, *args, **kwargs):
        queryset = self.queryset
        return queryset.filter(user_id=self.kwargs["id"]).annotate(
            following=Count("user__following", distinct=True),
            followers=Count("user__followers", distinct=True),
            liked=Count("user_likes", distinct=True),
            blocked=Count("user__blocked_users", distinct=True),
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

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset
        if self.action in ("list", "retrieve"):
            queryset = queryset.annotate(
                likes_count=Count(
                    "likes",
                    distinct=True,
                ),
                comments_count=Count(
                    "comments",
                    distinct=True,
                ),

            )
        if user.is_authenticated:
            following_users = Follower.objects.filter(
                follower=user
            ).values_list("following_id", flat=True)

            queryset = queryset.annotate(
                priority=Case(
                    When(owner_id__in=following_users, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).order_by("-priority", "created_at")
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


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
        return Response(
            {"detail": "Like deleted successfully."},
            status=status.HTTP_204_NO_CONTENT)


class CommentsView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        post_id = get_object_or_404(Post, pk=pk)
        commentaries = Comment.objects.filter(post=post_id)
        serializer = CommentsListPostSerializer(commentaries, many=True)
        return Response(serializer.data)

    def post(self, request, pk, *args, **kwargs):
        post_id = get_object_or_404(Post, pk=pk)
        body = request.data.get("body")
        if not body:
            return Response(
                {"detail": "Body is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        commentary = Comment.objects.create(
            post=post_id,
            user=request.user,
            body=body
        )

        serializer = CommentsListPostSerializer(commentary)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk, comment_id, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk)
        comment = get_object_or_404(Comment, pk=comment_id, post=post)
        if comment.user != request.user:
            return Response(
                {"detail": "You do not have permission to delete this comment."},
                status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return Response(
            {"detail": "Comment deleted successfully."},
            status=status.HTTP_204_NO_CONTENT)


class BlockedUserView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        owner = request.user
        blocked_users = owner.blocked_users.all()
        serializer = BlockedListUserSerializer(blocked_users, many=True)
        return Response(serializer.data)

    def post(self, request, pk, *args, **kwargs):
        user = get_object_or_404(User, pk=pk)
        blocker = self.request.user
        if user == blocker:
            return Response(
                {"detail": "You can not block yourself."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Blocked.objects.filter(blocker=blocker, blocked=user).exists():
            return Response(
                {"detail": f"{user.username} already blocked."},
                status=status.HTTP_400_BAD_REQUEST
            )
        blocked_user = Blocked.objects.create(
            blocker=request.user,
            blocked=user
        )
        return Response(
            {"detail": f"{user.username} blocked successfully."},
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, pk, *args, **kwargs):
        user = get_object_or_404(User, pk=pk)
        blocker = self.request.user
        if user == self.request.user:
            return Response(
                {"detail": "You can not unblock yourself."},
                status=status.HTTP_400_BAD_REQUEST
            )

        blocked_in_bd = Blocked.objects.filter(
            blocker=blocker,
            blocked=user
        )
        if not blocked_in_bd.exists():
            return Response(
                {"detail": f"{user.username} already unblocked."},
                status=status.HTTP_400_BAD_REQUEST)

        blocked_in_bd.delete()
        return Response(
            {f"{user} unblocked successfully."},
            status=status.HTTP_204_NO_CONTENT)


class ProfileView(generics.RetrieveAPIView, UpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = self.request.user
        profile = User.objects.filter(id=user.id).annotate(
            following_count=Count('following', distinct=True),
            followers_count=Count('followers', distinct=True),
            liked=Count('likes', distinct=True),
            blocked=Count('blocked_users', distinct=True)
        ).first()
        return profile


class LikedPostView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        likes = Like.objects.filter(user=user)
        serializer = LikedPostSerializer(likes, many=True)
        return Response(serializer.data)
