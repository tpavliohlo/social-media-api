from rest_framework import serializers

from core.models import Profile, Post, Like


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

    class Meta:
        model = Post
        fields = ["id", "title", "owner", "created_at"]


class PostRetrieveSerializer(PostSerializer):
    class Meta:
        model = Post
        fields = PostSerializer.Meta.fields + ["body"]


class LikesListPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ["id", "user"]


class LikeCreatePostSerializer(LikesListPostSerializer):
    class Meta:
        model = Like
        fields = LikesListPostSerializer.Meta.fields + ["post"]