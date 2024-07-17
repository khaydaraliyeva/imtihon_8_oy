import os.path
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
import random
import string
# Create your models here.


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=50, blank=True, null=True)
    lastname = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=150, blank=True, null=True)
    phone_number = models.CharField(max_length=13, blank=True, null=True)
    date_of_birth = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to='profile_image/', null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)

    def generate_verification_code(self):
        self.verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        self.save()

    def __str__(self):
        return f'{self.firstname} {self.lastname}'


class Lesson(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


def validate_video_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_ext = ['.mp4', '.mov', '.avi', '.mkv']
    if not ext.lower() in valid_ext:
        raise ValidationError(f'Notogri fayl kengaytmasi. Qabul qilinadigon kengaytmalar: {valid_ext}')


def validate_video_size(value):
    filesize = value.size
    if filesize > 500 * 1024 * 1024:  # 500 MB
        raise ValidationError("Fayl hajmi 500 MB dan oshmasligi kerak.")


class Video(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=50)
    video = models.FileField(upload_to='lesson_videos/', validators=[validate_video_extension, validate_video_size], null=True)
    description = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now_add=True)


class LikeLesson(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    like = models.BooleanField(default=False)
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('lesson', 'user')

    def save(self, *args, **kwargs):
        if LikeLesson.objects.filter(lesson=self.lesson, user=self.user).exists():
            raise ValidationError('Bu foydalanuvchi bu darsni allaqachon yoqtirgan.')
        super(LikeLesson, self).save(*args, **kwargs)


class DislikeLesson(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    dislike = models.BooleanField(default=False)
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('lesson', 'user')

    def save(self, *args, **kwargs):
        if DislikeLesson.objects.filter(lesson=self.lesson, user=self.user).exists():
            raise ValidationError('Bu foydalanuvchi bu darsni allaqachon yoqtirmagan.')
        super(DislikeLesson, self).save(*args, **kwargs)


class Comment(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.lesson.title}'


class View(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'View by {self.user.username} on {self.lesson.title}'


