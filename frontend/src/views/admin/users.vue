<template>
  <div class="page-container">
    <el-card class="mb-base">
      <div class="page-header">
        <h1 class="page-title">用户管理</h1>
        <div class="flex gap-base">
          <el-button type="primary" @click="handleAddUser" v-permission="'user:create'">
            <el-icon><Plus /></el-icon>新增用户
          </el-button>
          <el-button @click="refreshUserList">
            <el-icon><Refresh /></el-icon>刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <el-card class="mb-base">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="用户名">
          <el-input v-model="filterForm.username" placeholder="请输入用户名" clearable />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="filterForm.email" placeholder="请输入邮箱" clearable />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="filterForm.role" placeholder="请选择角色" clearable>
            <el-option
              v-for="role in roleOptions"
              :key="role.value"
              :label="role.label"
              :value="role.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="请选择状态" clearable>
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>搜索
          </el-button>
          <el-button @click="resetFilter">
            <el-icon><Refresh /></el-icon>重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table v-loading="loading" :data="userList" border stripe style="width: 100%">
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="phone" label="手机号" min-width="120" />
        <el-table-column prop="roles" label="角色" min-width="150">
          <template #default="scope">
            <el-tag
              v-for="role in scope.row.roles"
              :key="role"
              :type="getRoleTagType(role) as any"
              class="role-tag"
              effect="plain"
            >
              {{ getRoleName(role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录时间" min-width="180">
          <template #default="scope">
            {{ scope.row.last_login ? formatDateTime(scope.row.last_login) : '未登录' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status ? 'success' : 'danger'">
              {{ scope.row.status ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="250">
          <template #default="scope">
            <el-tooltip effect="dark" content="查看详情" placement="top">
              <el-button
                type="primary"
                link
                @click="handleViewUser(scope.row)"
                v-permission="'user:view'"
              >
                <el-icon><View /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip effect="dark" content="编辑用户" placement="top">
              <el-button
                type="primary"
                link
                @click="handleEditUser(scope.row)"
                v-permission="'user:edit'"
              >
                <el-icon><Edit /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip effect="dark" content="分配角色" placement="top">
              <el-button
                type="warning"
                link
                @click="handleAssignRoles(scope.row)"
                v-permission="'user:assignRole'"
              >
                <el-icon><SetUp /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip
              effect="dark"
              :content="scope.row.status ? '禁用用户' : '启用用户'"
              placement="top"
            >
              <el-button
                :type="scope.row.status ? 'danger' : 'success'"
                link
                @click="handleToggleStatus(scope.row)"
                v-permission="'user:toggle'"
              >
                <el-icon><component :is="scope.row.status ? 'Close' : 'Check'" /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip effect="dark" content="重置密码" placement="top">
              <el-button
                type="info"
                link
                @click="handleResetPassword(scope.row)"
                v-permission="'user:resetPwd'"
              >
                <el-icon><Key /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip effect="dark" content="删除用户" placement="top">
              <el-button
                type="danger"
                link
                @click="handleDeleteUser(scope.row)"
                v-permission="'user:delete'"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <div class="flex justify-center mt-base">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 用户表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? '新增用户' : dialogType === 'edit' ? '编辑用户' : '用户详情'"
      width="600px"
      destroy-on-close
    >
      <el-form
        ref="userFormRef"
        :model="userForm"
        :rules="userRules"
        label-width="100px"
        status-icon
        :disabled="dialogType === 'view'"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="userForm.username"
            placeholder="请输入用户名"
            :disabled="dialogType === 'edit'"
          />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="userForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="dialogType === 'add'">
          <el-input
            v-model="userForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword" v-if="dialogType === 'add'">
          <el-input
            v-model="userForm.confirmPassword"
            type="password"
            placeholder="请确认密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-switch v-model="userForm.status" :active-value="true" :inactive-value="false" />
        </el-form-item>
        <el-form-item label="角色" prop="roles" v-if="dialogType !== 'edit'">
          <el-select v-model="userForm.roles" multiple placeholder="请选择角色" style="width: 100%">
            <el-option
              v-for="role in roleOptions"
              :key="role.value"
              :label="role.label"
              :value="role.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitUserForm" v-if="dialogType !== 'view'"
            >确定</el-button
          >
        </span>
      </template>
    </el-dialog>

    <!-- 角色分配对话框 -->
    <el-dialog v-model="roleDialogVisible" title="分配角色" width="500px" destroy-on-close>
      <el-form label-width="80px">
        <el-form-item label="用户">
          <el-input :modelValue="selectedUser.username" disabled />
        </el-form-item>
        <el-form-item label="角色">
          <el-checkbox-group v-model="selectedRoles">
            <el-checkbox v-for="role in roleOptions" :key="role.value" :label="role.value">
              {{ role.label }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="roleDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitRoleAssignment">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 密码重置对话框 -->
    <el-dialog v-model="passwordDialogVisible" title="重置密码" width="500px" destroy-on-close>
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="100px"
        status-icon
      >
        <el-form-item label="用户">
          <el-input :modelValue="selectedUser.username" disabled />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            placeholder="请输入新密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            placeholder="请确认新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="passwordDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitPasswordReset">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts">
// 引入权限指令
import { vPermission } from '@/utils/validation/permission';

// 注册指令
const customDirectives = {
  directives: {
    permission: vPermission,
  }
};
</script>

<script setup lang="ts">
  import { ref, reactive, onMounted, nextTick } from 'vue';
  import { ElMessage, ElMessageBox, FormInstance, FormItemRule } from 'element-plus';
  import { formatDateTime } from '@/utils/format';
  import {
    Plus,
    View,
    Edit,
    SetUp,
    Key,
    Delete,
    Search,
    Refresh,
    Check,
    Close,
  } from '@element-plus/icons-vue';

  // 模拟用户数据
  interface User {
    id: string;
    username: string;
    email: string;
    phone: string;
    roles: string[];
    last_login: string | null;
    status: boolean;
    created_at: string;
    updated_at: string;
  }

  // 模拟角色数据
  const roleOptions = [
    { value: 'admin', label: '管理员' },
    { value: 'operator', label: '操作员' },
    { value: 'viewer', label: '访客' },
    { value: 'customer', label: '客户' },
  ];

  // 列表数据
  const loading = ref(false);
  const userList = ref<User[]>([]);
  const currentPage = ref(1);
  const pageSize = ref(10);
  const total = ref(0);

  // 筛选表单
  const filterForm = reactive({
    username: '',
    email: '',
    role: '',
    status: undefined as boolean | undefined,
  });

  // 用户表单
  const dialogVisible = ref(false);
  const dialogType = ref<'add' | 'edit' | 'view'>('add');
  const userFormRef = ref<FormInstance>();
  const userForm = reactive({
    id: '',
    username: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    status: true,
    roles: [] as string[],
  });

  // 表单验证规则
  const validateConfirmPassword = (rule: any, value: string, callback: any) => {
    if (value !== userForm.password) {
      callback(new Error('两次输入的密码不一致'));
    } else {
      callback();
    }
  };

  const userRules = {
    username: [
      { required: true, message: '请输入用户名', trigger: 'blur' },
      { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' },
    ],
    email: [
      { required: true, message: '请输入邮箱', trigger: 'blur' },
      { type: 'email' as const, message: '请输入正确的邮箱地址', trigger: 'blur' },
    ],
    phone: [{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }],
    password: [
      { required: true, message: '请输入密码', trigger: 'blur' },
      { min: 6, message: '密码长度不能少于6个字符', trigger: 'blur' },
    ],
    confirmPassword: [
      { required: true, message: '请确认密码', trigger: 'blur' },
      { validator: validateConfirmPassword, trigger: 'blur' },
    ],
    roles: [{ required: true, message: '请选择角色', trigger: 'change' }],
  };

  // 角色分配对话框
  const roleDialogVisible = ref(false);
  const selectedUser = ref<User>({} as User);
  const selectedRoles = ref<string[]>([]);

  // 密码重置对话框
  const passwordDialogVisible = ref(false);
  const passwordFormRef = ref<FormInstance>();
  const passwordForm = reactive({
    userId: '',
    newPassword: '',
    confirmPassword: '',
  });

  // 密码重置表单验证规则
  const validatePasswordConfirm = (rule: any, value: string, callback: any) => {
    if (value !== passwordForm.newPassword) {
      callback(new Error('两次输入的密码不一致'));
    } else {
      callback();
    }
  };

  const passwordRules = {
    newPassword: [
      { required: true, message: '请输入新密码', trigger: 'blur' },
      { min: 6, message: '密码长度不能少于6个字符', trigger: 'blur' },
    ],
    confirmPassword: [
      { required: true, message: '请确认新密码', trigger: 'blur' },
      { validator: validatePasswordConfirm, trigger: 'blur' },
    ],
  };

  // 模拟API调用
  const fetchUserList = async () => {
    loading.value = true;
    try {
      // 模拟后端API请求
      await new Promise(resolve => setTimeout(resolve, 500));

      // 模拟用户数据
      const mockUsers = Array.from({ length: 23 }, (_, i) => ({
        id: `user-${i + 1}`,
        username: `user${i + 1}`,
        email: `user${i + 1}@example.com`,
        phone: `1380000${(i + 1).toString().padStart(4, '0')}`,
        roles: i === 0 ? ['admin'] : i < 5 ? ['operator'] : i < 10 ? ['viewer'] : ['customer'],
        last_login:
          i < 15 ? new Date(Date.now() - Math.random() * 10000000000).toISOString() : null,
        status: i < 20,
        created_at: new Date(Date.now() - 30000000000).toISOString(),
        updated_at: new Date(Date.now() - 10000000000).toISOString(),
      }));

      // 筛选
      let filteredUsers = [...mockUsers];
      if (filterForm.username) {
        filteredUsers = filteredUsers.filter(user =>
          user.username.toLowerCase().includes(filterForm.username.toLowerCase()),
        );
      }
      if (filterForm.email) {
        filteredUsers = filteredUsers.filter(user =>
          user.email.toLowerCase().includes(filterForm.email.toLowerCase()),
        );
      }
      if (filterForm.role) {
        filteredUsers = filteredUsers.filter(user => user.roles.includes(filterForm.role));
      }
      if (filterForm.status !== undefined) {
        filteredUsers = filteredUsers.filter(user => user.status === filterForm.status);
      }

      total.value = filteredUsers.length;

      // 分页
      const start = (currentPage.value - 1) * pageSize.value;
      const end = start + pageSize.value;
      userList.value = filteredUsers.slice(start, end);

      // 记录用户操作
      logUserAction('查询用户列表');
    } catch (error) {
      console.error('获取用户列表失败:', error);
      ElMessage.error('获取用户列表失败');
    } finally {
      loading.value = false;
    }
  };

  // 搜索
  const handleSearch = () => {
    currentPage.value = 1;
    fetchUserList();
  };

  // 重置筛选条件
  const resetFilter = () => {
    filterForm.username = '';
    filterForm.email = '';
    filterForm.role = '';
    filterForm.status = undefined;
    handleSearch();
  };

  // 刷新用户列表
  const refreshUserList = () => {
    fetchUserList();
  };

  // 分页处理
  const handleSizeChange = (val: number) => {
    pageSize.value = val;
    fetchUserList();
  };

  const handleCurrentChange = (val: number) => {
    currentPage.value = val;
    fetchUserList();
  };

  // 获取角色名称
  const getRoleName = (roleCode: string): string => {
    const role = roleOptions.find(r => r.value === roleCode);
    return role ? role.label : roleCode;
  };

  // 获取角色标签类型
  const getRoleTagType = (roleCode: string): string => {
    switch (roleCode) {
      case 'admin':
        return 'danger';
      case 'operator':
        return 'warning';
      case 'viewer':
        return 'info';
      case 'customer':
        return 'success';
      default:
        return '';
    }
  };

  // 新增用户
  const handleAddUser = () => {
    dialogType.value = 'add';
    userForm.id = '';
    userForm.username = '';
    userForm.email = '';
    userForm.phone = '';
    userForm.password = '';
    userForm.confirmPassword = '';
    userForm.status = true;
    userForm.roles = [];
    dialogVisible.value = true;

    nextTick(() => {
      userFormRef.value?.resetFields();
    });
  };

  // 查看用户
  const handleViewUser = (row: User) => {
    dialogType.value = 'view';
    userForm.id = row.id;
    userForm.username = row.username;
    userForm.email = row.email;
    userForm.phone = row.phone;
    userForm.status = row.status;
    userForm.roles = [...row.roles];
    dialogVisible.value = true;
  };

  // 编辑用户
  const handleEditUser = (row: User) => {
    dialogType.value = 'edit';
    userForm.id = row.id;
    userForm.username = row.username;
    userForm.email = row.email;
    userForm.phone = row.phone;
    userForm.status = row.status;
    userForm.roles = [...row.roles];
    dialogVisible.value = true;

    nextTick(() => {
      userFormRef.value?.clearValidate();
    });
  };

  // 提交用户表单
  const submitUserForm = async () => {
    if (!userFormRef.value) return;

    await userFormRef.value.validate(async valid => {
      if (valid) {
        try {
          loading.value = true;

          // 模拟API调用
          await new Promise(resolve => setTimeout(resolve, 500));

          if (dialogType.value === 'add') {
            // 模拟添加用户成功
            ElMessage.success('添加用户成功');
            logUserAction(`新增用户: ${userForm.username}`);
          } else {
            // 模拟编辑用户成功
            ElMessage.success('更新用户成功');
            logUserAction(`编辑用户: ${userForm.username}`);
          }

          dialogVisible.value = false;
          fetchUserList();
        } catch (error) {
          console.error('保存用户失败:', error);
          ElMessage.error('保存用户失败');
        } finally {
          loading.value = false;
        }
      }
    });
  };

  // 分配角色
  const handleAssignRoles = (row: User) => {
    selectedUser.value = row;
    selectedRoles.value = [...row.roles];
    roleDialogVisible.value = true;
  };

  // 提交角色分配
  const submitRoleAssignment = async () => {
    try {
      loading.value = true;

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500));

      // 更新本地数据
      const userIndex = userList.value.findIndex(user => user.id === selectedUser.value.id);
      if (userIndex !== -1) {
        userList.value[userIndex].roles = [...selectedRoles.value];
      }

      ElMessage.success('角色分配成功');
      logUserAction(
        `为用户 ${selectedUser.value.username} 分配角色: ${selectedRoles.value.join(', ')}`,
      );
      roleDialogVisible.value = false;
    } catch (error) {
      console.error('角色分配失败:', error);
      ElMessage.error('角色分配失败');
    } finally {
      loading.value = false;
    }
  };

  // 切换用户状态
  const handleToggleStatus = async (row: User) => {
    try {
      loading.value = true;

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500));

      // 更新本地数据
      const userIndex = userList.value.findIndex(user => user.id === row.id);
      if (userIndex !== -1) {
        userList.value[userIndex].status = !row.status;
      }

      ElMessage.success(`用户已${row.status ? '禁用' : '启用'}`);
      logUserAction(`${row.status ? '禁用' : '启用'}用户: ${row.username}`);
    } catch (error) {
      console.error('更新用户状态失败:', error);
      ElMessage.error('更新用户状态失败');
    } finally {
      loading.value = false;
    }
  };

  // 重置密码
  const handleResetPassword = (row: User) => {
    selectedUser.value = row;
    passwordForm.userId = row.id;
    passwordForm.newPassword = '';
    passwordForm.confirmPassword = '';
    passwordDialogVisible.value = true;

    nextTick(() => {
      passwordFormRef.value?.resetFields();
    });
  };

  // 提交密码重置
  const submitPasswordReset = async () => {
    if (!passwordFormRef.value) return;

    await passwordFormRef.value.validate(async valid => {
      if (valid) {
        try {
          loading.value = true;

          // 模拟API调用
          await new Promise(resolve => setTimeout(resolve, 500));

          ElMessage.success('密码重置成功');
          logUserAction(`重置用户 ${selectedUser.value.username} 的密码`);
          passwordDialogVisible.value = false;
        } catch (error) {
          console.error('密码重置失败:', error);
          ElMessage.error('密码重置失败');
        } finally {
          loading.value = false;
        }
      }
    });
  };

  // 删除用户
  const handleDeleteUser = (row: User) => {
    ElMessageBox.confirm(`确定要删除用户 ${row.username} 吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
      .then(async () => {
        try {
          loading.value = true;

          // 模拟API调用
          await new Promise(resolve => setTimeout(resolve, 500));

          // 从本地列表中移除
          userList.value = userList.value.filter(user => user.id !== row.id);
          total.value--;

          ElMessage.success('删除用户成功');
          logUserAction(`删除用户: ${row.username}`);
        } catch (error) {
          console.error('删除用户失败:', error);
          ElMessage.error('删除用户失败');
        } finally {
          loading.value = false;
        }
      })
      .catch(() => {
        // 取消删除
      });
  };

  // 记录用户操作
  const logUserAction = (action: string) => {
    console.log(`[${new Date().toISOString()}] ${action}`);
    // 实际应用中这里会调用API将操作记录保存到后端
  };

  // 初始化
  onMounted(() => {
    fetchUserList();
  });
</script>

<style scoped>
  .role-tag {
    margin-right: var(--el-spacing-small);
    &:last-child {
      margin-right: 0;
    }
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: var(--el-spacing-base);
  }
</style>
