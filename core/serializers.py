from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.models import Profile, Post, Like, Comment, Blocked, Follower
from user.serializers import UserSerializer


class RetrieveProfileSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    following = serializers.ReadOnlyField(source='user.following')
    followers = serializers.ReadOnlyField(source='user.followers')

    class Meta:
        model = Profile
        fields = [
            'id',
            'user',
            'username',
            'following',
            'followers',
            'description',
            'privacy_settings',
        ]


class PostSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "owner",
            "likes_count",
            "comments_count",
            "created_at"
        ]


class CommentsSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Comment
        fields = ["id", "user", "body", "created_at"]


class PostRetrieveSerializer(PostSerializer):
    comments = CommentsSerializer(many=True)

    class Meta:
        model = Post
        fields = (PostSerializer.Meta.fields + ["body", "comments"])


class LikesListPostSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Like
        fields = ["id", "user"]


class LikeCreatePostSerializer(LikesListPostSerializer):
    class Meta:
        model = Like
        fields = LikesListPostSerializer.Meta.fields + ["post"]


class CommentsListPostSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Comment
        fields = ["id", "user", "body"]


class BlockedListUserSerializer(serializers.ModelSerializer):
    blocked = serializers.ReadOnlyField(source='blocked.username')

    class Meta:
        model = Blocked
        fields = ["id", "blocked"]


class BlockedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blocked
        fields = ["id", "blocked"]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["image_profile","description", "privacy_settings"]
        extra_kwargs = {
            "description": {"required": False},
            "allow_blank": True,
        }


class UserProfileSerializer(UserSerializer):
    description = serializers.CharField(
        source='profile.description',
        required=False,
        allow_blank=True
    )
    privacy_settings = serializers.ChoiceField(
        source="profile.privacy_settings",
        choices=Profile.PrivacySettings.choices,
        required=False,
    )
    image_profile = serializers.ImageField(
        source="profile.image_profile",
        required=False,
    )

    following_count = serializers.IntegerField(read_only=True)
    followers_count = serializers.IntegerField(read_only=True)
    liked = serializers.IntegerField(read_only=True)
    blocked = serializers.IntegerField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "image_profile",
            "username",
            "email",
            "description",
            "privacy_settings",
            "following_count",
            "followers_count",
            "liked",
            "blocked",
        ]
        read_only_fields = ["id"]

        extra_kwargs = {
            "password": {"write_only": True, "min_length": 6},
        }

    def update(self, instance, validated_data):
        user_data = validated_data.copy()

        if "username" in user_data:
            instance.username = user_data.get("username", instance.username)
        if "email" in user_data:
            instance.email = user_data.get("email", instance.email)

            instance.save()

            profile_data = user_data.get("profile", {})

            if profile_data:
                profile, created = Profile.objects.get_or_create(
                    user=instance,
                )
                profile.description = profile_data.get(
                    "description",
                    profile.description
                )
                if "image_profile" in profile_data:
                    profile.image_profile = profile_data.get(
                        "image_profile",
                        profile.image_profile
                    )
                profile.save()

            return instance


class LikedPostSerializer(serializers.ModelSerializer):
    post = serializers.SlugRelatedField(slug_field='title', read_only=True)

    class Meta:
        model = Like
        fields = ["id", "post", "created_at"]


class FollowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follower
        fields = ["id", "follower", "following"]
