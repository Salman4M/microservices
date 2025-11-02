from django.core.exceptions import ValidationError


def not_only_whitespace(value):
    if not value.strip():
        raise ValidationError('Cannot consist of only whitespace')
    
    if len(value.strip()) < 3:
        raise ValidationError('Must be at least 2 characters long')
