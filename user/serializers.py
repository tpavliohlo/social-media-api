from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.models import Follower
from user.models import User


class UserFollowersFollowingSerializer(serializers.ModelSerializer):
    followers = serializers.SerializerMethodField()
    following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["username", "followers", "following"]

    def get_followers(self, obj):
        followers = Follower.objects.filter(following=obj)
        return [follower.follower.username for follower in followers]

    def get_following(self, obj):
        following = Follower.objects.filter(follower=obj)
        return [follow.following.username for follow in following]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "email", "is_staff", "password"]
        read_only_fields = ["id", "is_staff"]
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 6}
        }

        def create(self, validated_data):
            """Create User with encrypted password."""
            return get_user_model().objects.create_user(**validated_data)

        def update(self, instance, validated_data):
            """Update User with encrypted password."""
            password = validated_data.pop("password", None)
            user = super().update(instance, validated_data)
            if password:
                user.set_password(password)
                user.save()
            return user
