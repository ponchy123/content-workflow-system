from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile, Role, UserLoginLog

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    用户档案序列化器
    """
    class Meta:
        model = UserProfile
        fields = ['real_name', 'gender', 'birthday', 'address', 'bio']


class UserSerializer(serializers.ModelSerializer):
    """
    用户序列化器
    """
    profile = UserProfileSerializer(required=False)
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['user_id', 'username', 'email', 'mobile', 'password', 'confirm_password',
                'name', 'avatar', 'department', 'position',
                'is_active', 'date_joined', 'profile']
        read_only_fields = ['date_joined']

    def validate(self, attrs):
        if 'password' in attrs:
            if not attrs.get('confirm_password'):
                raise serializers.ValidationError({"confirm_password": "请确认密码"})
            if attrs['password'] != attrs['confirm_password']:
                raise serializers.ValidationError({"password": "两次密码不一致"})
            validate_password(attrs['password'])
        return attrs

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)
        
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        
        if profile_data:
            UserProfile.objects.create(user=user, **profile_data)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)
        
        if password:
            instance.set_password(password)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if profile_data and hasattr(instance, 'profile'):
            for attr, value in profile_data.items():
                setattr(instance.profile, attr, value)
            instance.profile.save()
        elif profile_data:
            UserProfile.objects.create(user=instance, **profile_data)
        
        return instance


class RoleSerializer(serializers.ModelSerializer):
    """
    角色序列化器
    """
    class Meta:
        model = Role
        fields = ['role_id', 'role_name', 'role_code', 'description', 'status']
        read_only_fields = []

    def validate_role_code(self, value):
        """
        验证角色代码唯一性
        """
        if Role.objects.filter(role_code=value).exists():
            raise serializers.ValidationError("角色代码已存在")
        return value


class UserLoginLogSerializer(serializers.ModelSerializer):
    """
    用户登录日志序列化器
    """
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UserLoginLog
        fields = ['username', 'ip_address', 'user_agent', 'login_time',
                'login_type', 'status', 'remarks']
        read_only_fields = ['login_time'] 