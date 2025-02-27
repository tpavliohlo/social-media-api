from rest_framework import serializers

from core.models import Profile


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