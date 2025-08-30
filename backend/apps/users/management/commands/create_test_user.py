"""
创建测试用户的管理命令
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from apps.users.models import User
from apps.core.models import Tenant, Role, Permission


class Command(BaseCommand):
    help = '创建测试用户用于开发和测试'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='用户名 (默认: admin)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='密码 (默认: admin123)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@quanttrade.com',
            help='邮箱 (默认: admin@quanttrade.com)'
        )
        parser.add_argument(
            '--tenant-name',
            type=str,
            default='测试租户',
            help='租户名称 (默认: 测试租户)'
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']
        tenant_name = options['tenant_name']

        try:
            # 创建或获取租户
            tenant, created = Tenant.objects.get_or_create(
                name=tenant_name,
                defaults={
                    'description': '用于开发和测试的租户',
                    'is_active': True,
                    'max_users': 100,
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ 创建租户: {tenant.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ 租户已存在: {tenant.name}')
                )

            # 检查用户是否已存在
            if User.objects.filter(username=username, tenant=tenant).exists():
                self.stdout.write(
                    self.style.WARNING(f'⚠️ 用户已存在: {username}@{tenant.name}')
                )
                return

            # 创建用户
            user = User.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                tenant=tenant,
                is_active=True,
                is_staff=True,
                is_superuser=True,
                is_tenant_admin=True,
                first_name='管理员',
                last_name='测试',
            )

            self.stdout.write(
                self.style.SUCCESS(f'✅ 创建用户成功!')
            )
            self.stdout.write(f'   用户名: {username}')
            self.stdout.write(f'   密码: {password}')
            self.stdout.write(f'   邮箱: {email}')
            self.stdout.write(f'   租户: {tenant.name}')
            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS('🎉 现在可以使用这个账户登录系统了!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 创建用户失败: {str(e)}')
            )