from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator


# User
class UserSerializer(serializers.ModelSerializer):
    is_shop_owner = serializers.BooleanField(read_only=True)
    slug = serializers.SlugField(read_only=True)
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone_number', 'slug', 'created_at','is_shop_owner']

# Register
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

#Login


User = get_user_model()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")

        data['user'] = user
        return data

# reset password
User = get_user_model()
token_generator = PasswordResetTokenGenerator()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(label="Email")


class PasswordResetConfirmSerializer(serializers.Serializer):
    
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=6, label="Yeni şifrə")
    confirm_password = serializers.CharField(write_only=True, min_length=6, label="Yeni şifrə (təkrar)")

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Şifrələr uyğun gəlmir."})

        try:
            uid = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=uid)
        except Exception:
            raise serializers.ValidationError({"uid": "İstifadəçi tapılmadı və ya link səhvdir."})

        if not token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError({"token": "Bu link etibarsız və ya müddəti bitib."})

        attrs['user'] = user
        return attrs
