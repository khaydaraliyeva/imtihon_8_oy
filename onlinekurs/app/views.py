from django.contrib.auth.models import User
from django.db.models import Q, Count
from rest_framework import status, permissions, generics, mixins
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login
from .serializers import UserSerializer, LoginSerializer, UserRegistrationSerializer, LogoutSerializer
from rest_framework import viewsets
from .models import UserProfile, Lesson, Video, LikeLesson, DislikeLesson, Comment, View
from .serializers import (UserProfileSerializer, LessonSerializer,VerifyEmailSerializer, VideoSerializer,
                          LikeLessonSerializer, DislikeLessonSerializer, CommentSerializer, ViewSerializer)
from .utils import send_verification_email, send_mail_to_email


class UserRegistrationAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        user_profile, created = UserProfile.objects.get_or_create(user=user)

        if created:
            user_profile.generate_verification_code()
            user_profile.save()

            emails = [user.email]
            subject = "Hush kelibsiz online kurs dunyosiga"
            message = f"Salom {user.username}, bizning sajifamizda ro'yxatdan o'tganingizdan hursandmiz. Tasdiqlash kodi: {user_profile.verification_code}"
            send_mail_to_email(emails, subject, message)

        return Response({'detail': 'Verification code sent to email.'}, status=status.HTTP_201_CREATED)


class VerifyEmailAPIView(generics.GenericAPIView):
    serializer_class = VerifyEmailSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        verification_code = serializer.validated_data['verification_code']

        try:
            user = User.objects.get(username=username)
            user_profile = UserProfile.objects.get(user=user, verification_code=verification_code)

            user_profile.is_verified = True
            user_profile.verification_code = None
            user_profile.save()

            user.is_active = True
            user.save()

            return Response({'detail': 'Email verified successfully.'}, status=status.HTTP_200_OK)
        except (User.DoesNotExist, UserProfile.DoesNotExist):
            return Response({'detail': 'Invalid verification code or username.'}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(mixins.CreateModelMixin, generics.GenericAPIView):
    serializer_class = LoginSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer()
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = authenticate(request, username=username, password=password)
        login(request, user)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user == instance.user:
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        else:
            return Response({'message': 'You are not allowed to update this profile'}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user == instance.user:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'message': 'You are not allowed to delete this profile'}, status=status.HTTP_403_FORBIDDEN)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lesson = serializer.save(user=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.is_superuser or instance.user == request.user:
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        else:
            return Response({'message': 'You are not allowed to update this lesson'}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.is_superuser or instance.user == request.user:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'message': 'You are not allowed to delete this lesson'}, status=status.HTTP_403_FORBIDDEN)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        likes = LikeLesson.objects.filter(lesson=instance)
        dislikes = DislikeLesson.objects.filter(lesson=instance)
        existing_view = View.objects.filter(lesson=instance, user=request.user).first()
        if not existing_view:
            View.objects.create(lesson=instance, user=request.user)
        views = View.objects.filter(lesson=instance)
        videos = Video.objects.filter(lesson=instance)
        video_serializer = VideoSerializer(videos, many=True)
        data = {
            'lesson': LessonSerializer(instance).data,
            'videos': video_serializer.data,
            'likes': likes.count(),
            'dislikes': dislikes.count(),
            'views': views.count()
        }
        return Response(data)


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

    def create(self, request, *args, **kwargs):
        lesson_id = request.data.get('lesson')
        lesson = Lesson.objects.get(pk=lesson_id)
        if request.user.is_superuser or lesson.user == request.user:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            video = serializer.save(user=request.user)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'You are not allowed to create a video for this lesson'},
                            status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.is_superuser or instance.lesson.user == request.user:
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        else:
            return Response({'message': 'You are not allowed to update this video'}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.is_superuser or instance.lesson.user == request.user:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'message': 'You are not allowed to delete this video'}, status=status.HTTP_403_FORBIDDEN)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        data = {
            'video': VideoSerializer(instance).data,
        }
        return Response(data)


class LikeLessonViewSet(viewsets.ModelViewSet):
    queryset = LikeLesson.objects.all()
    serializer_class = LikeLessonSerializer

    def create(self, request, *args, **kwargs):
        lesson_id = request.data.get('lesson')
        existing_dislike = DislikeLesson.objects.filter(lesson=lesson_id, user=request.user).first()
        if existing_dislike:
            existing_dislike.delete()

        existing_like = LikeLesson.objects.filter(lesson=lesson_id, user=request.user).first()
        if existing_like:
            existing_like.delete()
            return Response({'message': 'Like removed successfully'}, status=status.HTTP_204_NO_CONTENT)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DislikeLessonViewSet(viewsets.ModelViewSet):
    queryset = DislikeLesson.objects.all()
    serializer_class = DislikeLessonSerializer

    def create(self, request, *args, **kwargs):
        lesson_id = request.data.get('lesson')
        existing_like = LikeLesson.objects.filter(lesson=lesson_id, user=request.user).first()
        if existing_like:
            existing_like.delete()

        existing_dislike = DislikeLesson.objects.filter(lesson=lesson_id, user=request.user).first()
        if existing_dislike:
            existing_dislike.delete()
            return Response({'message': 'Dislike removed successfully'}, status=status.HTTP_204_NO_CONTENT)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user == instance.user:
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        else:
            return Response({'message': 'You are not allowed to update this comment'}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user == instance.user:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'message': 'You are not allowed to delete this comment'}, status=status.HTTP_403_FORBIDDEN)


class LessonSearchAPIView(generics.ListAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        return Lesson.objects.filter(
            Q(title__icontains=query) |
            Q(video__title__icontains=query)
        ).distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MostLikedLessonsAPIView(generics.ListAPIView):
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Lesson.objects.annotate(like_count=Count('likelesson')).order_by('-like_count')


class MostViewedLessonsAPIView(generics.ListAPIView):
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Lesson.objects.annotate(view_count=Count('views')).order_by('-view_count')


class NotifyAllUsersAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        json_template = {
            "subject": "",
            "message": ""
        }
        return Response(json_template)

    def post(self, request, *args, **kwargs):
        subject = request.data.get('subject')
        message = request.data.get('message')
        if not subject or not message:
            return Response({'error': 'Subject and message are required.'}, status=status.HTTP_400_BAD_REQUEST)

        emails = list(User.objects.values_list('email', flat=True))
        send_mail_to_email(emails, subject, message)

        return Response({'detail': 'Notification sent to all users.'}, status=status.HTTP_200_OK)

