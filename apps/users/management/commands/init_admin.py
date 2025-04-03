from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.users.models import Role

User = get_user_model()

class Command(BaseCommand):
    help = '初始化管理员用户'

    def handle(self, *args, **options):
        try:
            # 检查是否已存在管理员用户
            if User.objects.filter(username='admin').exists():
                self.stdout.write(self.style.WARNING('管理员用户已存在'))
                return

            # 创建管理员角色
            admin_role, created = Role.objects.get_or_create(
                code='admin',
                defaults={
                    'name': '管理员',
                    'description': '系统管理员角色',
                    'is_system': True
                }
            )

            # 创建管理员用户
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )

            # 设置用户档案
            admin_user.department = '系统管理'
            admin_user.position = '系统管理员'
            admin_user.save()

            # 创建用户档案
            admin_user.profile.real_name = '系统管理员'
            admin_user.profile.save()

            self.stdout.write(self.style.SUCCESS('管理员用户创建成功'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'创建管理员用户失败: {str(e)}')) 