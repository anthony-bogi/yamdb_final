from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Расширенная модель работы с пользователями."""
    CHOICES = (
        ('user', 'user'),
        ('moderator', 'moderator'),
        ('admin', 'admin'),
    )
    username = models.CharField(
        max_length=150,
        unique=True
    )
    email = models.EmailField(
        verbose_name='e-mail адрес',
        max_length=254,
        unique=True
    )
    bio = models.TextField(
        'Биография',
        blank=True,
        null=True
    )
    role = models.CharField(
        max_length=15,
        choices=CHOICES,
        default='user'
    )
    confirmation_code = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    password = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    USERNAME_FIELD = 'username'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name="unique_fields"
            ),
        ]

    def __str__(self) -> str:
        return self.username
