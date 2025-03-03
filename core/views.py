from django.db.models import (
    Count,
    Value,
    Case,
    When,
    IntegerField,
    Q
)
from django.shortcuts import render
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse
)
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
from core.permissions import (
    IsOwnerOrReadOnly,
    CanLikePostPermission,
    CanCommentOnPostPermission,
)
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
    FollowerSerializer,
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
        profile_public = Profile.PrivacySettings.PUBLIC
        private_public = Profile.PrivacySettings.PRIVATE

        if not user.is_authenticated:
            queryset = queryset.filter(
                owner__profile__privacy_settings=profile_public,
            )

        else:
            following_users = Follower.objects.filter(
                follower=user
            ).values_list("following_id", flat=True)

            blocked_users = Blocked.objects.filter(
                blocker=user
            ).values_list("blocked", flat=True)

            queryset = queryset.annotate(
                priority=Case(
                    When(
                        owner_id__in=following_users,
                        then=Value(1)
                    ),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).order_by("-priority", "-created_at")

            queryset = queryset.filter(
                Q(owner__profile__privacy_settings=profile_public) |
                Q(owner__profile__privacy_settings=private_public,
                  owner__in=following_users,)
                  ).exclude(
                    owner__in=blocked_users
                ).annotate(
                likes_count=Count("likes", distinct=True),
                comments_count=Count("comments", distinct=True),
            ).select_related("owner").prefetch_related("comments__user")


        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LikesView(views.APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get likes for a post",
        description="Retrieve a list of users who liked a specific post.",
        responses={200: LikesListPostSerializer},
        parameters=[
            OpenApiParameter(
                "pk",
                description="ID of the post to fetch likes for",
                required=True,
                type=int
            )
        ]
    )

    def get(self, request, pk, *args, **kwargs):
        post_id = get_object_or_404(Post, pk=pk)
        likes = Like.objects.filter(post=post_id).select_related("user")
        serializer = LikesListPostSerializer(likes, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Like a post.",
        description="Create a like for a specific post by"
                    "the authenticated user. "
                    "You can like a post only once.",
        request=LikeCreatePostSerializer,
        responses={
            201: LikeCreatePostSerializer,
            400: OpenApiResponse(description="You have already liked this post.")
        },
        parameters=[
            OpenApiParameter(
                "pk",
                description="ID of the post to like",
                required=True,
                type=int
            )
        ]
    )

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

    @extend_schema(
        summary="Unlike a post.",
        description="Remove the like from a specific "
                    "post by the authenticated user. "
                    "You can only remove a like you hvae previuosly added.",
        responses={
            204: OpenApiResponse(description="Like deleted successfully."),
            400: OpenApiResponse(description="Ypu have not liked this post.")
        },
        parameters=[
            OpenApiParameter(
                "pk",
                description="ID of the post to unlike",
                required=True,
                type=int
            )
        ]
    )

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

    @extend_schema(
        summary="Get comments for a post",
        description="Retrieve a list of comments for a specific post.",
        responses={200: CommentsListPostSerializer},
        parameters=[
            OpenApiParameter(
                "pk",
                description="ID of the post to fetch comments for",
                required=True,
                type=int
            )
        ]
    )

    def get(self, request, pk, *args, **kwargs):
        post_id = get_object_or_404(Post, pk=pk)
        comments = Comment.objects.filter(post=post_id).select_related("user")
        serializer = CommentsListPostSerializer(comments, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create a comment for a post",
        description="Create a new comment for a specific post.",
        request=CommentsListPostSerializer,
        responses={
            201: CommentsListPostSerializer,
            400: OpenApiResponse(description="Body is required.")
        },
        parameters=[
            OpenApiParameter(
                "pk",
                description="ID of the post to add the comment for",
                required=True,
                type=int
            )
        ]
    )

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

    @extend_schema(
        summary="Delete a comment",
        description="Delete a specific comment if a current user is the owner of the comment.",
        responses={
            204: OpenApiResponse(description="Comment deleted successfully."),
            403: OpenApiResponse(description="Forbidden to delete this comment."),
        },
        parameters=[
            OpenApiParameter(
                "pk",
                description="ID of the post",
                required=True,
                type=int
            ),
            OpenApiParameter(
                "comment_id",
                description="ID of the comment to delete",
                required=True,
                type=int
            )
        ]
    )

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

    @extend_schema(
        summary="Get list of blocked user",
        description="Retrieve the list of "
                    "users that the authenticated user has blocked.",
        responses={200:BlockedListUserSerializer},
    )

    def get(self, request, *args, **kwargs):
        owner = request.user
        blocked_users = owner.blocked_users.all()
        serializer = BlockedListUserSerializer(blocked_users, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Block a user",
        description="Block a specific user. "
                    "You cannot block yourself, and you can only block a user once.",
        request=None,
        responses={
            201: OpenApiResponse(
                description="User blocked successfully."
            ),
            400: OpenApiResponse(
                description="You cannot block yourself "
                            "or user is already blocked."
            )
        },
        parameters=[
            OpenApiParameter(
                "pk",
                description="ID of the user to block",
                required=True,
                type=int
            )
        ]
    )

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

    @extend_schema(
        summary="Unblock a user",
        description="Unblock a specific user that "
                    "was previously blocked. You cannot unblock yourself.",
        responses={
            204: OpenApiResponse(
                description="You cannot unblock yourself "
                            "or user was not blocked."
            ),
            400: OpenApiResponse(
                description="You cannot unblock yourself "
                            "or user was not blocked."
            )
        },
        parameters=[
            OpenApiParameter(
                "pk",
                description="ID of the user to unblock",
                required=True,
                type=int
            )
        ]
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
        likes = Like.objects.filter(user=user).select_related("post")
        serializer = LikedPostSerializer(likes, many=True)
        return Response(serializer.data)


class FollowSerializer(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        user = self.request.user
        profile_pk = get_object_or_404(User, pk=pk)
        existing_following = Follower.objects.filter(
            follower=user,
            following=profile_pk
        ).first()
        if existing_following:
            return Response(
                {"detail": "You have already followed!"},
                status=status.HTTP_400_BAD_REQUEST
            )
        create_follower = Follower.objects.create(
            follower=user,
            following=profile_pk
        )
        serializer = FollowerSerializer(create_follower)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk, *args, **kwargs):
        user = self.request.user
        profile_pk = get_object_or_404(User, pk=pk)
        existing_following = Follower.objects.filter(
            follower=user,
            following=profile_pk
        ).first()
        if not existing_following:
            return Response(
                {"detail": "You have not already follower!"},
                status=status.HTTP_400_BAD_REQUEST
            )
        existing_following.delete()
        return Response(
            {"detail": "Unfollowed successfully!"},
            status=status.HTTP_204_NO_CONTENT
        )
