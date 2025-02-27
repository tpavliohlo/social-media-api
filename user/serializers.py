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
