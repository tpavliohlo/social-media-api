from django.db.models import Count
from django.shortcuts import render
from rest_framework import generics

from core.models import Profile
from core.serializers import RetrieveProfileSerializer


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
