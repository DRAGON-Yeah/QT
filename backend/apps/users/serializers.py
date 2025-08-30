"""
用户管理序列化器

本模块包含用户管理相关的所有序列化器，用于处理用户、角色、权限等数据的序列化和反序列化。
支持多租户架构，确保数据隔离和权限控制。

主要功能：
- 用户CRUD操作的数据序列化
- 角色和权限管理的数据处理
- 用户密码修改和安全验证
- 批量角色分配操作
"""
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from apps.core.models import Role, Permission
from .models import User, UserProfile, UserRole


class PermissionSerializer(serializers.ModelSerializer):
    """
    权限序列化器
    
    用于序列化权限模型数据，提供权限信息的标准化输出格式。
    主要用于角色管理和权限分配功能。
    """
    
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'category', 'description']


class RoleSerializer(serializers.ModelSerializer):
    """
    角色序列化器
    
    处理角色数据的序列化和反序列化，支持角色的创建、更新和权限分配。
    包含角色关联的权限信息和用户统计数据。
    """
    # 只读字段：显示角色的所有权限详情
    permissions = PermissionSerializer(many=True, read_only=True)
    
    # 写入字段：用于创建/更新角色时指定权限ID列表
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="权限ID列表，用于分配权限给角色"
    )
    
    # 计算字段：显示拥有此角色的用户数量
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'description', 'role_type', 'is_active',
            'permissions', 'permission_ids', 'user_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_user_count(self, obj):
        """
        获取拥有此角色的用户数量
        
        Args:
            obj: 角色实例
            
        Returns:
            int: 激活状态的用户数量
        """
        return obj.users.filter(is_active=True).count()
    
    def create(self, validated_data):
        """
        创建角色
        
        创建新角色并分配指定的权限。如果提供了permission_ids，
        会自动关联相应的权限到新创建的角色。
        
        Args:
            validated_data: 验证后的数据
            
        Returns:
            Role: 创建的角色实例
        """
        permission_ids = validated_data.pop('permission_ids', [])
        role = super().create(validated_data)
        
        # 如果提供了权限ID列表，则分配权限
        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids)
            role.permissions.set(permissions)
        
        return role
    
    def update(self, instance, validated_data):
        """
        更新角色
        
        更新角色信息并重新分配权限。如果提供了permission_ids，
        会替换角色的所有权限；如果为None则不修改权限。
        
        Args:
            instance: 要更新的角色实例
            validated_data: 验证后的数据
            
        Returns:
            Role: 更新后的角色实例
        """
        permission_ids = validated_data.pop('permission_ids', None)
        role = super().update(instance, validated_data)
        
        # 如果明确提供了权限ID列表（包括空列表），则更新权限
        if permission_ids is not None:
            permissions = Permission.objects.filter(id__in=permission_ids)
            role.permissions.set(permissions)
        
        return role


class UserRoleSerializer(serializers.ModelSerializer):
    """
    用户角色关联序列化器
    
    用于序列化用户和角色的关联关系，包含角色分配的详细信息，
    如分配时间、分配者、过期时间等审计信息。
    """
    # 关联字段：显示角色名称
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    # 关联字段：显示角色描述
    role_description = serializers.CharField(source='role.description', read_only=True)
    
    # 关联字段：显示分配者用户名
    assigned_by_name = serializers.CharField(source='assigned_by.username', read_only=True)
    
    class Meta:
        model = UserRole
        fields = [
            'id', 'role', 'role_name', 'role_description',
            'assigned_at', 'assigned_by', 'assigned_by_name',
            'expires_at', 'is_active'
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    """
    用户配置序列化器
    
    处理用户个人配置信息的序列化，包括个人资料、通知设置、
    界面偏好等用户个性化配置数据。
    """
    
    class Meta:
        model = UserProfile
        fields = [
            'real_name', 'id_number', 'birth_date', 'address',
            'emergency_contact', 'emergency_phone', 'default_risk_level',
            'email_notifications', 'sms_notifications', 'push_notifications',
            'theme', 'settings'
        ]


class UserListSerializer(serializers.ModelSerializer):
    """
    用户列表序列化器
    
    用于用户列表页面的数据序列化，提供用户基本信息和状态摘要。
    优化了查询性能，只包含列表展示所需的关键字段。
    """
    # 关联字段：显示租户名称
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    # 计算字段：显示用户的所有角色名称
    role_names = serializers.SerializerMethodField()
    
    # 计算字段：格式化的最后登录时间
    last_login_display = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'phone',
            'is_active', 'is_tenant_admin', 'tenant_name', 'role_names',
            'last_login', 'last_login_display', 'date_joined'
        ]
    
    def get_role_names(self, obj):
        """
        获取用户角色名称列表
        
        Args:
            obj: 用户实例
            
        Returns:
            list: 激活状态的角色名称列表
        """
        return [role.name for role in obj.roles.filter(is_active=True)]
    
    def get_last_login_display(self, obj):
        """
        获取最后登录时间的显示格式
        
        Args:
            obj: 用户实例
            
        Returns:
            str: 格式化的登录时间或"从未登录"
        """
        if obj.last_login:
            return obj.last_login.strftime('%Y-%m-%d %H:%M:%S')
        return '从未登录'


class UserDetailSerializer(serializers.ModelSerializer):
    """
    用户详情序列化器
    
    用于用户详情页面和编辑功能的完整数据序列化。
    包含用户的所有信息、角色、权限和配置数据。
    支持用户信息的更新和角色分配。
    """
    # 关联字段：显示租户名称
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    # 嵌套序列化：显示用户的所有角色详情
    roles = RoleSerializer(many=True, read_only=True)
    
    # 写入字段：用于更新用户角色
    role_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="角色ID列表，用于分配角色给用户"
    )
    
    # 嵌套序列化：显示用户配置信息
    profile = UserProfileSerializer(read_only=True)
    
    # 嵌套序列化：显示用户角色关联的详细信息
    user_roles = UserRoleSerializer(source='userrole_set', many=True, read_only=True)
    
    # 计算字段：显示用户的所有权限
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'phone',
            'is_active', 'is_tenant_admin', 'tenant', 'tenant_name',
            'roles', 'role_ids', 'profile', 'user_roles', 'permissions',
            'last_login', 'last_login_ip', 'last_activity',
            'password_changed_at', 'failed_login_attempts', 'locked_until',
            'language', 'timezone_name', 'date_joined'
        ]
        read_only_fields = [
            'id', 'tenant', 'last_login', 'last_login_ip', 'last_activity',
            'password_changed_at', 'failed_login_attempts', 'locked_until',
            'date_joined'
        ]
    
    def get_permissions(self, obj):
        """
        获取用户所有权限
        
        Args:
            obj: 用户实例
            
        Returns:
            list: 用户拥有的所有权限代码列表
        """
        return list(obj.get_all_permissions())
    
    def update(self, instance, validated_data):
        """
        更新用户信息
        
        更新用户基本信息并重新分配角色。如果提供了role_ids，
        会清除用户的所有现有角色并分配新的角色。
        
        Args:
            instance: 要更新的用户实例
            validated_data: 验证后的数据
            
        Returns:
            User: 更新后的用户实例
        """
        role_ids = validated_data.pop('role_ids', None)
        
        # 更新用户基本信息
        user = super().update(instance, validated_data)
        
        # 更新用户角色
        if role_ids is not None:
            # 清除现有角色关联
            user.roles.clear()
            
            # 添加新角色
            if role_ids:
                roles = Role.objects.filter(
                    id__in=role_ids,
                    tenant=user.tenant,
                    is_active=True
                )
                for role in roles:
                    user.add_role(role)
        
        return user


class UserCreateSerializer(serializers.ModelSerializer):
    """
    用户创建序列化器
    
    专门用于创建新用户的序列化器，包含密码验证、唯一性检查、
    角色分配和用户配置初始化等功能。确保多租户环境下的数据隔离。
    """
    # 密码字段：写入专用，最小长度8位
    password = serializers.CharField(
        write_only=True, 
        min_length=8,
        help_text="用户密码，最少8位字符"
    )
    
    # 密码确认字段：用于验证密码输入一致性
    password_confirm = serializers.CharField(
        write_only=True,
        help_text="确认密码，必须与密码字段一致"
    )
    
    # 角色ID列表：用于为新用户分配角色
    role_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="要分配给用户的角色ID列表"
    )
    
    # 用户配置数据：嵌套的用户配置信息
    profile_data = UserProfileSerializer(
        required=False,
        help_text="用户个人配置信息"
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'is_tenant_admin',
            'role_ids', 'profile_data', 'language', 'timezone_name'
        ]
    
    def validate(self, attrs):
        """
        验证用户创建数据
        
        执行密码确认验证、用户名和邮箱的租户内唯一性检查。
        
        Args:
            attrs: 待验证的属性字典
            
        Returns:
            dict: 验证通过的属性字典
            
        Raises:
            ValidationError: 当验证失败时抛出
        """
        # 验证密码确认
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': '两次输入的密码不一致'})
        
        # 获取当前请求上下文
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.tenant:
            tenant = request.user.tenant
            
            # 验证用户名在当前租户内的唯一性
            if User.objects.filter(
                tenant=tenant,
                username=attrs['username']
            ).exists():
                raise serializers.ValidationError({'username': '用户名已存在'})
            
            # 验证邮箱在当前租户内的唯一性（如果提供了邮箱）
            if attrs.get('email'):
                if User.objects.filter(
                    tenant=tenant,
                    email=attrs['email']
                ).exists():
                    raise serializers.ValidationError({'email': '邮箱已存在'})
        
        return attrs
    
    def create(self, validated_data):
        """
        创建新用户
        
        使用UserManagementService创建用户，确保正确的租户隔离、
        角色分配和用户配置初始化。
        
        Args:
            validated_data: 验证后的数据
            
        Returns:
            User: 创建的用户实例
            
        Raises:
            ValidationError: 当创建失败时抛出
        """
        from .services import UserManagementService
        
        # 移除序列化器专用字段
        validated_data.pop('password_confirm')
        role_ids = validated_data.pop('role_ids', [])
        profile_data = validated_data.pop('profile_data', {})
        
        # 获取当前租户
        request = self.context.get('request')
        tenant = request.user.tenant if request and hasattr(request, 'user') else None
        
        if not tenant:
            raise serializers.ValidationError('无法确定当前租户')
        
        # 将角色ID转换为角色名称
        role_names = []
        if role_ids:
            roles = Role.objects.filter(id__in=role_ids, tenant=tenant)
            role_names = [role.name for role in roles]
        
        # 使用服务层创建用户
        user = UserManagementService.create_user(
            tenant=tenant,
            roles=role_names,
            created_by=request.user if request else None,
            **validated_data
        )
        
        # 更新用户配置信息
        if profile_data:
            profile = user.profile
            for key, value in profile_data.items():
                setattr(profile, key, value)
            profile.save()
        
        return user


class UserPasswordChangeSerializer(serializers.Serializer):
    """
    用户密码修改序列化器
    
    处理用户密码修改请求，支持普通用户自主修改密码和管理员强制修改密码两种模式。
    包含密码验证、权限检查和安全性保障。
    """
    # 当前密码：普通修改模式下必需
    old_password = serializers.CharField(
        required=False,
        help_text="当前密码，普通修改模式下必需"
    )
    
    # 新密码：最小长度8位
    new_password = serializers.CharField(
        min_length=8,
        help_text="新密码，最少8位字符"
    )
    
    # 新密码确认：用于验证密码输入一致性
    new_password_confirm = serializers.CharField(
        help_text="确认新密码，必须与新密码字段一致"
    )
    
    # 强制修改标志：管理员可以强制修改用户密码
    force_change = serializers.BooleanField(
        default=False,
        help_text="是否强制修改，需要管理员权限"
    )
    
    def validate(self, attrs):
        """
        验证密码修改数据
        
        验证新密码确认、当前密码正确性和强制修改权限。
        
        Args:
            attrs: 待验证的属性字典
            
        Returns:
            dict: 验证通过的属性字典
            
        Raises:
            ValidationError: 当验证失败时抛出
        """
        # 验证新密码确认
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': '两次输入的密码不一致'})
        
        # 获取上下文中的用户和请求对象
        user = self.context.get('user')
        request = self.context.get('request')
        
        # 根据修改模式进行不同的验证
        if not attrs.get('force_change', False):
            # 普通修改模式：需要验证当前密码
            if not attrs.get('old_password'):
                raise serializers.ValidationError({'old_password': '请输入当前密码'})
            
            if not user.check_password(attrs['old_password']):
                raise serializers.ValidationError({'old_password': '当前密码错误'})
        else:
            # 强制修改模式：需要管理员权限
            if not (request and request.user.has_permission('user.change_password')):
                raise serializers.ValidationError('没有权限强制修改密码')
        
        return attrs
    
    def save(self):
        """
        保存新密码
        
        更新用户密码并保存到数据库。密码会自动进行哈希处理。
        
        Returns:
            User: 更新密码后的用户实例
        """
        user = self.context.get('user')
        new_password = self.validated_data['new_password']
        
        # 设置新密码（自动进行哈希处理）
        user.set_password(new_password)
        user.save()
        
        return user


class RoleAssignmentSerializer(serializers.Serializer):
    """
    角色分配序列化器
    
    处理批量角色分配操作，支持添加、移除和替换三种操作模式。
    确保多租户环境下的数据隔离和操作安全性。
    """
    # 用户ID列表：要操作的用户
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="要分配角色的用户ID列表"
    )
    
    # 角色ID列表：要分配的角色
    role_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="要分配的角色ID列表"
    )
    
    # 操作类型：添加、移除或替换
    action = serializers.ChoiceField(
        choices=['add', 'remove', 'replace'],
        help_text="操作类型：add(添加)、remove(移除)、replace(替换)"
    )
    
    # 过期时间：角色分配的过期时间（可选）
    expires_at = serializers.DateTimeField(
        required=False,
        help_text="角色过期时间，不设置则永不过期"
    )
    
    def validate(self, attrs):
        """
        验证角色分配数据
        
        验证用户和角色的存在性、租户归属和权限状态。
        
        Args:
            attrs: 待验证的属性字典
            
        Returns:
            dict: 验证通过的属性字典，包含用户和角色实例
            
        Raises:
            ValidationError: 当验证失败时抛出
        """
        request = self.context.get('request')
        tenant = request.user.tenant if request and hasattr(request, 'user') else None
        
        if not tenant:
            raise serializers.ValidationError('无法确定当前租户')
        
        # 验证用户是否存在且属于当前租户
        user_ids = attrs['user_ids']
        users = User.objects.filter(id__in=user_ids, tenant=tenant)
        if len(users) != len(user_ids):
            raise serializers.ValidationError('部分用户不存在或不属于当前租户')
        
        # 验证角色是否存在且属于当前租户
        role_ids = attrs['role_ids']
        roles = Role.objects.filter(id__in=role_ids, tenant=tenant, is_active=True)
        if len(roles) != len(role_ids):
            raise serializers.ValidationError('部分角色不存在或不属于当前租户')
        
        # 将查询到的实例添加到验证数据中
        attrs['users'] = users
        attrs['roles'] = roles
        
        return attrs
    
    def save(self):
        """
        执行角色分配操作
        
        根据指定的操作类型批量处理用户角色分配，记录操作结果。
        
        Returns:
            list: 操作结果列表，包含每个用户的处理详情
        """
        users = self.validated_data['users']
        roles = self.validated_data['roles']
        action = self.validated_data['action']
        expires_at = self.validated_data.get('expires_at')
        
        request = self.context.get('request')
        assigned_by = request.user if request else None
        
        results = []
        
        # 遍历每个用户执行角色操作
        for user in users:
            user_result = {
                'user_id': user.id, 
                'username': user.username, 
                'roles': []
            }
            
            # 遍历每个角色执行具体操作
            for role in roles:
                try:
                    if action == 'add':
                        # 添加角色：如果不存在则创建关联
                        user_role, created = UserRole.objects.get_or_create(
                            user=user,
                            role=role,
                            defaults={
                                'assigned_by': assigned_by,
                                'expires_at': expires_at,
                                'is_active': True
                            }
                        )
                        user_result['roles'].append({
                            'role_id': role.id,
                            'role_name': role.name,
                            'action': 'added' if created else 'already_exists'
                        })
                    
                    elif action == 'remove':
                        # 移除角色：删除用户角色关联
                        deleted_count = UserRole.objects.filter(
                            user=user,
                            role=role
                        ).delete()[0]
                        
                        user_result['roles'].append({
                            'role_id': role.id,
                            'role_name': role.name,
                            'action': 'removed' if deleted_count > 0 else 'not_found'
                        })
                    
                    elif action == 'replace':
                        # 替换角色：先清除所有角色，再添加新角色
                        if role == roles[0]:  # 只在处理第一个角色时清除
                            user.roles.clear()
                        
                        user_role, created = UserRole.objects.get_or_create(
                            user=user,
                            role=role,
                            defaults={
                                'assigned_by': assigned_by,
                                'expires_at': expires_at,
                                'is_active': True
                            }
                        )
                        
                        user_result['roles'].append({
                            'role_id': role.id,
                            'role_name': role.name,
                            'action': 'replaced'
                        })
                
                except Exception as e:
                    # 记录操作异常
                    user_result['roles'].append({
                        'role_id': role.id,
                        'role_name': role.name,
                        'action': 'error',
                        'error': str(e)
                    })
            
            results.append(user_result)
        
        return results


class LoginSerializer(serializers.Serializer):
    """
    用户登录序列化器
    
    处理用户登录请求的数据验证，包含用户名和密码的基本验证。
    """
    username = serializers.CharField(
        max_length=150,
        help_text="用户名"
    )
    
    password = serializers.CharField(
        write_only=True,
        help_text="密码"
    )
    
    def validate(self, attrs):
        """验证登录数据"""
        username = attrs.get('username')
        password = attrs.get('password')
        
        if not username or not password:
            raise serializers.ValidationError('用户名和密码不能为空')
        
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """
    密码修改序列化器
    
    处理用户自主修改密码的请求，需要验证当前密码。
    """
    old_password = serializers.CharField(
        write_only=True,
        help_text="当前密码"
    )
    
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="新密码，最少8位字符"
    )
    
    new_password_confirm = serializers.CharField(
        write_only=True,
        help_text="确认新密码"
    )
    
    def validate(self, attrs):
        """验证密码修改数据"""
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        # 验证新密码确认
        if new_password != new_password_confirm:
            raise serializers.ValidationError({'new_password_confirm': '两次输入的密码不一致'})
        
        # 验证当前密码
        user = self.context.get('user')
        if user and not user.check_password(old_password):
            raise serializers.ValidationError({'old_password': '当前密码错误'})
        
        return attrs


class PasswordResetSerializer(serializers.Serializer):
    """
    密码重置序列化器
    
    处理管理员重置用户密码的请求。
    """
    user_id = serializers.UUIDField(
        help_text="要重置密码的用户ID"
    )
    
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="新密码，最少8位字符"
    )
    
    new_password_confirm = serializers.CharField(
        write_only=True,
        help_text="确认新密码"
    )
    
    def validate(self, attrs):
        """验证密码重置数据"""
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        # 验证新密码确认
        if new_password != new_password_confirm:
            raise serializers.ValidationError({'new_password_confirm': '两次输入的密码不一致'})
        
        return attrs