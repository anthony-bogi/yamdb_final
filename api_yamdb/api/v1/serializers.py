from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator
from reviews.models import Category, Comment, Genre, Review, Title
from users.models import User

from .utility import username_is_valid


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор для жанров."""

    class Meta:
        exclude = ('id',)
        model = Genre


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий."""

    class Meta:
        exclude = ('id',)
        model = Category


class TitleSerializer(serializers.ModelSerializer):
    """Сериализатор для произведений."""
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(many=True, read_only=True)
    rating = serializers.IntegerField(
        source='reviews__score__avg', read_only=True
    )

    class Meta:
        model = Title
        fields = '__all__'


class TitleSerializerCreate(serializers.ModelSerializer):
    """Сериализатор для работы с произведениями при создании."""
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug'
    )
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug',
        many=True
    )

    class Meta:
        model = Title
        fields = '__all__'


class AdminUserSerializer(serializers.ModelSerializer):
    """Сериализатор для Администратора."""
    username = serializers.CharField(
        max_length=150,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    email = serializers.EmailField(
        max_length=254,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role'
        )
        model = User
        lookup_field = 'username'
        extra_kwargs = {
            'url': {'lookup_field': 'username', },
        }
        validators = (
            UniqueTogetherValidator(
                queryset=User.objects.all(),
                fields=['username', 'email']
            ),
        )

    def validate(self, data):
        if not username_is_valid(data.get('username')):
            raise serializers.ValidationError(
                "Неожиданный паттерн"
            )
        if data.get('username') == 'me':
            raise serializers.ValidationError('Недопустимое имя пользователя.')
        return data


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя."""
    username = serializers.CharField(
        max_length=150,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    email = serializers.EmailField(
        max_length=254,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    role = serializers.CharField(max_length=15, read_only=True)

    class Meta:
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role'
        )
        model = User
        lookup_field = 'username'
        extra_kwargs = {
            'url': {'lookup_field': 'username', },
        }
        validators = (
            UniqueTogetherValidator(
                queryset=User.objects.all(),
                fields=['username', 'email']
            ),
        )

    def validate(self, data):
        if not username_is_valid(data.get('username')):
            raise serializers.ValidationError(
                "Неожиданный паттерн"
            )
        if data.get('username') == 'me':
            raise serializers.ValidationError('Недопустимое имя пользователя.')
        return data


class ConfirmationCodeSerializer(serializers.ModelSerializer):
    """Сериализатор для получения кода подтверждения, регистрации."""

    class Meta:
        fields = (
            'email',
            'username'
        )
        model = User
        validators = (
            UniqueTogetherValidator(
                queryset=User.objects.all(),
                fields=['username', 'email']
            ),
        )

    def validate(self, data):
        if not username_is_valid(data.get('username')):
            raise serializers.ValidationError(
                "Неожиданный паттерн"
            )
        if User.objects.filter(username=data.get('username')).exists():
            raise serializers.ValidationError(
                'Имя уже занято другим пользователем'
            )
        if data.get('username') == 'me':
            raise serializers.ValidationError('Недопустимое имя пользователя.')
        if User.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError(
                'E-mail уже занят другим пользователем'
            )
        return data


class TokenSerializer(serializers.Serializer):
    """Сериализатор для получения токена."""
    username = serializers.CharField(
        max_length=150,
        write_only=True,
    )
    confirmation_code = serializers.CharField(
        max_length=254,
        write_only=True
    )

    def validate(self, data):
        user = get_object_or_404(User, username=data['username'])
        user_1 = User.objects.filter(
            username=user.username,
            confirmation_code=data['confirmation_code']
        ).exists()
        if not user_1:
            raise serializers.ValidationError(
                'Такого пользователя не существует.'
            )
        return data


class ReviewSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели отзывов.
    """
    author = serializers.SlugRelatedField(
        slug_field='username',
        default=serializers.CurrentUserDefault(),
        read_only=True
    )
    title = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True
    )

    def validate(self, data):
        request = self.context['request']
        author = request.user
        title_id = self.context['view'].kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        if (
            request.method == 'POST'
            and Review.objects.filter(title=title, author=author).exists()
        ):
            raise ValidationError()
        return data

    class Meta:
        fields = '__all__'
        model = Review


class CommentSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели комментариев.
    """
    author = serializers.SlugRelatedField(
        slug_field='username',
        default=serializers.CurrentUserDefault(),
        read_only=True
    )
    review = serializers.SlugRelatedField(
        slug_field='text',
        read_only=True
    )

    class Meta:
        model = Comment
        fields = '__all__'
