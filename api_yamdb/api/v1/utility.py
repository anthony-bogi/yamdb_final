from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.regex_helper import _lazy_re_compile

username_validator = RegexValidator(
    _lazy_re_compile(r'^[\w.@+-]+\Z'),
    message='Enter a valid username.',
    code='invalid',
)


def username_is_valid(username):
    try:
        username_validator(username)
        return True
    except ValidationError:
        return False
