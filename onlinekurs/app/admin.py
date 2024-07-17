from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import UserProfile, Lesson, Video, LikeLesson, DislikeLesson, Comment, View


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'firstname', 'lastname', 'email', 'is_verified', 'created')
    search_fields = ('user__username', 'firstname', 'lastname', 'email')
    readonly_fields = ('verification_code',)


class VideoInline(admin.TabularInline):
    model = Video
    extra = 1


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1


class ViewInline(admin.TabularInline):
    model = View
    extra = 1


class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created', 'update', 'likes_count', 'dislikes_count', 'views_count')
    search_fields = ('title', 'user__username')
    inlines = [VideoInline, CommentInline, ViewInline]

    def likes_count(self, obj):
        return LikeLesson.objects.filter(lesson=obj).count()
    likes_count.short_description = 'Likes'

    def dislikes_count(self, obj):
        return DislikeLesson.objects.filter(lesson=obj).count()
    dislikes_count.short_description = 'Dislikes'

    def views_count(self, obj):
        return View.objects.filter(lesson=obj).count()
    views_count.short_description = 'Views'


class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'user', 'created', 'update')
    search_fields = ('title', 'lesson__title', 'user__username')


class LikeLessonAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'user', 'created_time')
    search_fields = ('lesson__title', 'user__username')


class DislikeLessonAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'user', 'created_time')
    search_fields = ('lesson__title', 'user__username')


class CommentAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'user', 'content', 'created_at', 'updated_at')
    search_fields = ('lesson__title', 'user__username', 'content')


class ViewAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'user', 'viewed_at')
    search_fields = ('lesson__title', 'user__username')


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(LikeLesson, LikeLessonAdmin)
admin.site.register(DislikeLesson, DislikeLessonAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(View, ViewAdmin)
