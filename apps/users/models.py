from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from apps.core.models import BaseModel


class User(AbstractUser):
    """用户表"""
    user_id = models.AutoField('用户ID', primary_key=True)
    username = models.CharField('用户名', max_length=150, unique=True)
    email = models.EmailField('邮箱', max_length=150, unique=True)
    mobile = models.CharField('手机号', max_length=11, unique=True)
    name = models.CharField('姓名', max_length=100)
    avatar = models.CharField('头像', max_length=200, null=True, blank=True)
    department = models.CharField('部门', max_length=100, null=True, blank=True)
    position = models.CharField('职位', max_length=100, null=True, blank=True)
    is_active = models.BooleanField('是否激活', default=True)
    is_staff = models.BooleanField('是否员工', default=False)
    is_superuser = models.BooleanField('是否超级管理员', default=False)
    last_login = models.DateTimeField('最后登录时间', null=True, blank=True)
    date_joined = models.DateTimeField('加入时间', auto_now_add=True)

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['mobile']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.username} ({self.name})"


class UserProfile(BaseModel):
    """
    用户档案
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    real_name = models.CharField('真实姓名', max_length=50, null=True, blank=True)
    gender = models.CharField('性别', max_length=10, choices=[('male', '男'), ('female', '女')], null=True, blank=True)
    birthday = models.DateField('生日', null=True, blank=True)
    address = models.CharField('地址', max_length=200, null=True, blank=True)
    bio = models.TextField('个人简介', null=True, blank=True)

    class Meta:
        verbose_name = '用户档案'
        verbose_name_plural = verbose_name
        db_table = 'user_profile'

    def __str__(self):
        return f"{self.user.username}的档案"


class Role(BaseModel):
    """角色表"""
    role_id = models.AutoField('角色ID', primary_key=True)
    role_name = models.CharField('角色名称', max_length=100, unique=True)
    role_code = models.CharField('角色代码', max_length=100, unique=True)
    description = models.TextField('描述', null=True, blank=True)
    status = models.BooleanField('状态', default=True)

    class Meta:
        db_table = 'roles'
        verbose_name = '角色'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['role_code']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.role_name} ({self.role_code})"


class Permission(BaseModel):
    """权限表"""
    permission_id = models.AutoField('权限ID', primary_key=True)
    permission_name = models.CharField('权限名称', max_length=100)
    permission_code = models.CharField('权限代码', max_length=100, unique=True)
    description = models.TextField('描述', null=True, blank=True)
    status = models.BooleanField('状态', default=True)

    class Meta:
        db_table = 'permissions'
        verbose_name = '权限'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['permission_code']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.permission_name} ({self.permission_code})"


class UserRole(BaseModel):
    """用户角色关联表"""
    user_role_id = models.AutoField('用户角色ID', primary_key=True)
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        db_column='user_id',
        to_field='user_id',
        verbose_name='用户'
    )
    role = models.ForeignKey(
        'Role',
        on_delete=models.CASCADE,
        db_column='role_id',
        to_field='role_id',
        verbose_name='角色'
    )
    status = models.BooleanField('状态', default=True)

    class Meta:
        db_table = 'user_roles'
        verbose_name = '用户角色'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['user', 'role']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.role.role_name}"


class RolePermission(BaseModel):
    """角色权限关联表"""
    role_permission_id = models.AutoField('角色权限ID', primary_key=True)
    role = models.ForeignKey(
        'Role',
        on_delete=models.CASCADE,
        db_column='role_id',
        to_field='role_id',
        verbose_name='角色'
    )
    permission = models.ForeignKey(
        'Permission',
        on_delete=models.CASCADE,
        db_column='permission_id',
        to_field='permission_id',
        verbose_name='权限'
    )
    status = models.BooleanField('状态', default=True)

    class Meta:
        db_table = 'role_permissions'
        verbose_name = '角色权限'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['role', 'permission']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.role.role_name} - {self.permission.permission_name}"


class UserLoginLog(BaseModel):
    """
    用户登录日志
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    ip_address = models.GenericIPAddressField('IP地址')
    user_agent = models.CharField('用户代理', max_length=255)
    login_time = models.DateTimeField('登录时间', default=timezone.now)
    login_type = models.CharField('登录方式', max_length=20, choices=[
        ('username', '用户名密码'),
        ('phone', '手机验证码'),
        ('social', '社交账号'),
    ])
    status = models.BooleanField('状态', default=True)
    remarks = models.TextField('备注', null=True, blank=True)

    class Meta:
        verbose_name = '登录日志'
        verbose_name_plural = verbose_name
        db_table = 'user_login_log'
        ordering = ['-login_time']

    def __str__(self):
        return f"{self.user.username} - {self.login_time}" 