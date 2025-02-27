from django.contrib import admin

from core.models import Profile, Post, Comment, Follower, Like, Blocked

admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(Follower)
admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(Blocked)
