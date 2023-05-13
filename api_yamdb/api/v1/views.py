from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from reviews.models import Category, Genre, Review, Title
from users.models import User

from .filters import TitleFilter
from .permissions import (IsAdminModeratorOwnerPermission,
                          IsAdminOrSuperuserPermission, TitlePermission)
from .serializers import (AdminUserSerializer, CategorySerializer,
                          CommentSerializer, ConfirmationCodeSerializer,
                          GenreSerializer, ReviewSerializer, TitleSerializer,
                          TitleSerializerCreate, TokenSerializer,
                          UserSerializer)


class TitleViewSet(viewsets.ModelViewSet):
    """Вьюсет для произведений."""
    queryset = Title.objects.all().annotate(
        Avg("reviews__score")
    ).order_by('name')
    serializer_class = TitleSerializerCreate
    permission_classes = [TitlePermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH', 'DELETE',):
            return TitleSerializerCreate
        return TitleSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """Вьюсет для категорий."""
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [TitlePermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ('name',)

    @action(
        detail=False, methods=['delete'],
        url_path=r'(?P<slug>\w+)',
        lookup_field='slug', url_name='category_slug'
    )
    def get_category(self, request, slug):
        category = self.get_object()
        serializer = CategorySerializer(category)
        category.delete()
        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)


class GenreViewSet(viewsets.ModelViewSet):
    """Вьюсет для жанров."""
    queryset = Genre.objects.all().order_by('name')
    serializer_class = GenreSerializer
    permission_classes = [TitlePermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    @action(
        detail=False, methods=['delete'],
        url_path=r'(?P<slug>\w+)',
        lookup_field='slug', url_name='category_slug'
    )
    def get_genre(self, request, slug):
        category = self.get_object()
        serializer = CategorySerializer(category)
        category.delete()
        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)


class UserViewSet(viewsets.ModelViewSet):
    """Работа с пользователями для администратора."""
    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = User.objects.all()
    permission_classes = (
        permissions.IsAuthenticated,
        IsAdminOrSuperuserPermission,
    )
    lookup_field = 'username'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)

    def get_serializer_class(self):
        if (
            self.request.user.role != 'admin'
            or self.request.user.is_superuser
        ):
            return UserSerializer
        return AdminUserSerializer

    @action(
        detail=False,
        url_path='me',
        methods=['get', 'patch'],
        permission_classes=[permissions.IsAuthenticated, ],
        queryset=User.objects.all()
    )
    def me(self, request):
        """
        Профиль пользователя с редактированием.
        Поле role редактирует только администратор.
        """
        user = get_object_or_404(User, id=request.user.id)
        if request.method == 'PATCH':
            serializer = UserSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = self.get_serializer(user, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = ConfirmationCodeSerializer(data=request.data)
    if User.objects.filter(username=request.data.get('username'),
                           email=request.data.get('email')).exists():
        user, created = User.objects.get_or_create(
            username=request.data.get('username')
        )
        if created is False:
            confirmation_code = default_token_generator.make_token(user)
            user.confirmation_code = confirmation_code
            user.save()
            return Response('Ваш токен обновлен!', status=status.HTTP_200_OK)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    user, created = User.objects.get_or_create(
        username=request.data.get('username')
    )
    confirmation_code = default_token_generator.make_token(user)
    user.confirmation_code = confirmation_code
    send_mail(f'Привет, {str(user.username)}! Ваш код подтверждения:',
              confirmation_code,
              settings.MAILING_EMAIL,
              [request.data['email']],
              fail_silently=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(http_method_names=['POST', ])
def token(request):
    """Получить токен."""
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    user = get_object_or_404(User, **data)
    refresh = RefreshToken.for_user(user)
    return Response(
        {'access': str(refresh.access_token)}, status=status.HTTP_201_CREATED
    )


class ReviewViewSet(viewsets.ModelViewSet):
    """
    View класс для запросов GET, POST, для списка всех отзывов произведения
    или GET, PUT, PATCH, DELETE для отзывов по id.
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAdminModeratorOwnerPermission]

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        return title.reviews.all()

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    """
    View класс для запросов GET, POST, для списка всех комментариев отзыва
    или GET, PUT, PATCH, DELETE для комментариев по id.
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAdminModeratorOwnerPermission]

    def get_queryset(self):
        review = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        return review.comments.all()

    def perform_create(self, serializer):
        review = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        serializer.save(author=self.request.user, review=review)
