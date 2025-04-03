<template>
  <div class="page-container">
    <el-card class="mb-base">
      <div class="page-header">
        <h1 class="page-title">角色管理</h1>
        <div class="flex gap-base">
          <el-button type="primary" @click="handleAddRole">
            <el-icon><Plus /></el-icon>新增角色
          </el-button>
          <el-button @click="fetchRoleList">
            <el-icon><Refresh /></el-icon>刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <el-card>
      <el-table v-loading="loading" :data="roleList" border stripe style="width: 100%">
        <el-table-column type="index" width="50" align="center" />
        <el-table-column prop="name" label="角色名称" min-width="120" />
        <el-table-column prop="code" label="角色编码" min-width="120" />
        <el-table-column
          prop="description"
          label="角色描述"
          min-width="200"
          show-overflow-tooltip
        />
        <el-table-column prop="created_at" label="创建时间" min-width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status ? 'success' : 'danger'" size="small">
              {{ scope.row.status ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="scope">
            <el-tooltip effect="dark" content="编辑角色" placement="top">
              <el-button type="primary" link @click="handleEditRole(scope.row)">
                <el-icon><Edit /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip effect="dark" content="分配权限" placement="top">
              <el-button type="success" link @click="handleAssignPermissions(scope.row)">
                <el-icon><Setting /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip effect="dark" content="查看用户" placement="top">
              <el-button type="info" link @click="handleViewUsers(scope.row)">
                <el-icon><User /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip :content="scope.row.status ? '禁用角色' : '启用角色'" placement="top">
              <el-button
                :type="scope.row.status ? 'warning' : 'success'"
                link
                @click="handleToggleStatus(scope.row)"
              >
                <el-icon>
                  <component :is="scope.row.status ? 'CircleClose' : 'CircleCheck'" />
                </el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip effect="dark" content="删除角色" placement="top">
              <el-button
                type="danger"
                link
                @click="handleDeleteRole(scope.row)"
                v-permission="'role:delete'"
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

    <!-- 角色表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? '新增角色' : '编辑角色'"
      width="600px"
      destroy-on-close
    >
      <el-form ref="roleFormRef" :model="roleForm" :rules="roleRules" label-width="100px">
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="roleForm.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="角色编码" prop="code">
          <el-input
            v-model="roleForm.code"
            placeholder="请输入角色编码"
            :disabled="dialogType === 'edit'"
          />
        </el-form-item>
        <el-form-item label="角色描述" prop="description">
          <el-input
            v-model="roleForm.description"
            type="textarea"
            placeholder="请输入角色描述"
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-switch v-model="roleForm.status" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitRoleForm">确定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 分配权限对话框 -->
    <el-dialog v-model="permissionDialogVisible" title="分配权限" width="800px" destroy-on-close>
      <div v-if="currentRole.id" class="role-info">
        <h3>{{ currentRole.name }}</h3>
        <p>{{ currentRole.description }}</p>
      </div>

      <div class="permission-tree-container">
        <div class="permission-filter">
          <el-input v-model="permissionFilterText" placeholder="输入关键字进行过滤" clearable />
        </div>
        <el-tree
          ref="permissionTreeRef"
          :data="permissionTree"
          show-checkbox
          node-key="id"
          :props="{ label: 'name', children: 'children' }"
          :default-checked-keys="selectedPermissions"
          :filter-node-method="filterPermissionNode"
          @check="handlePermissionCheck"
        >
          <template #default="{ node, data }">
            <div class="permission-node">
              <span>{{ node.label }}</span>
              <el-tag v-if="data.code" size="small" effect="plain">{{ data.code }}</el-tag>
            </div>
          </template>
        </el-tree>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="permissionDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="savePermissions">确定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 查看用户对话框 -->
    <el-dialog v-model="userDialogVisible" title="角色用户列表" width="800px" destroy-on-close>
      <div v-if="currentRole.id" class="role-info">
        <h3>{{ currentRole.name }}</h3>
        <p>{{ currentRole.description }}</p>
      </div>

      <el-table v-loading="userLoading" :data="roleUserList" border stripe style="width: 100%">
        <el-table-column type="index" width="50" align="center" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="phone" label="手机号" min-width="120" />
        <el-table-column prop="lastLoginTime" label="最后登录时间" min-width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status ? 'success' : 'danger'" size="small">
              {{ scope.row.status ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="userCurrentPage"
          v-model:page-size="userPageSize"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="userTotal"
          @size-change="handleUserSizeChange"
          @current-change="handleUserCurrentChange"
        />
      </div>
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
  import { ref, reactive, watch, onMounted, nextTick } from 'vue';
  import { ElMessage, ElMessageBox, ElTree } from 'element-plus';
  import { formatDateTime } from '@/utils/format';
  import {
    Plus,
    Edit,
    Delete,
    Setting,
    User,
    Refresh,
    CircleCheck,
    CircleClose,
  } from '@element-plus/icons-vue';
  import type { FormInstance, FormRules } from 'element-plus';

  // 角色数据接口
  interface Role {
    id: string;
    name: string;
    code: string;
    description: string;
    status: boolean;
    created_at: string;
    updated_at: string;
  }

  // 权限数据接口
  interface Permission {
    id: string;
    name: string;
    code: string;
    description?: string;
    children?: Permission[];
  }

  // 用户数据接口
  interface User {
    id: string;
    username: string;
    email: string;
    phone: string;
    status: boolean;
    lastLoginTime: string;
  }

  // 列表数据
  const loading = ref(false);
  const roleList = ref<Role[]>([]);
  const currentPage = ref(1);
  const pageSize = ref(10);
  const total = ref(0);

  // 角色表单
  const dialogVisible = ref(false);
  const dialogType = ref<'add' | 'edit'>('add');
  const roleFormRef = ref<FormInstance>();
  const roleForm = reactive({
    id: '',
    name: '',
    code: '',
    description: '',
    status: true,
  });

  // 表单验证规则
  const roleRules = reactive<FormRules>({
    name: [
      { required: true, message: '请输入角色名称', trigger: 'blur' },
      { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' },
    ],
    code: [
      { required: true, message: '请输入角色编码', trigger: 'blur' },
      {
        pattern: /^[a-zA-Z_][a-zA-Z0-9_]*$/,
        message: '角色编码只能包含字母、数字和下划线，且以字母或下划线开头',
        trigger: 'blur',
      },
    ],
    description: [{ max: 200, message: '长度不能超过 200 个字符', trigger: 'blur' }],
  });

  // 权限分配
  const permissionDialogVisible = ref(false);
  const permissionTreeRef = ref<InstanceType<typeof ElTree>>();
  const permissionTree = ref<Permission[]>([]);
  const selectedPermissions = ref<string[]>([]);
  const permissionFilterText = ref('');
  const currentRole = ref<Role>({} as Role);

  // 角色用户列表
  const userDialogVisible = ref(false);
  const userLoading = ref(false);
  const roleUserList = ref<User[]>([]);
  const userCurrentPage = ref(1);
  const userPageSize = ref(10);
  const userTotal = ref(0);

  // 获取角色列表
  const fetchRoleList = async () => {
    loading.value = true;
    try {
      // 模拟后端API请求
      await new Promise(resolve => setTimeout(resolve, 500));

      // 模拟角色数据
      const mockRoles = Array.from({ length: 20 }, (_, i) => {
        const date = new Date();
        date.setTime(date.getTime() - Math.random() * 90 * 24 * 3600 * 1000);

        const roleTypes = [
          { name: '超级管理员', code: 'admin' },
          { name: '系统管理员', code: 'system' },
          { name: '数据分析员', code: 'analyst' },
          { name: '运营人员', code: 'operator' },
          { name: '普通用户', code: 'user' },
          { name: '客户经理', code: 'manager' },
          { name: '财务人员', code: 'finance' },
          { name: '审计人员', code: 'auditor' },
        ];

        const roleType =
          i < roleTypes.length
            ? roleTypes[i]
            : {
                name: `自定义角色${i - roleTypes.length + 1}`,
                code: `custom_${i - roleTypes.length + 1}`,
              };

        return {
          id: `role-${i + 1}`,
          name: roleType.name,
          code: roleType.code,
          description: `${roleType.name}的权限描述，可以访问特定功能和数据`,
          status: Math.random() > 0.2,
          created_at: date.toISOString(),
          updated_at: date.toISOString(),
        };
      });

      // 分页
      const start = (currentPage.value - 1) * pageSize.value;
      const end = start + pageSize.value;
      roleList.value = mockRoles.slice(start, end);
      total.value = mockRoles.length;
    } catch (error) {
      console.error('获取角色列表失败:', error);
      ElMessage.error('获取角色列表失败');
    } finally {
      loading.value = false;
    }
  };

  // 分页处理
  const handleSizeChange = (val: number) => {
    pageSize.value = val;
    fetchRoleList();
  };

  const handleCurrentChange = (val: number) => {
    currentPage.value = val;
    fetchRoleList();
  };

  // 新增角色
  const handleAddRole = () => {
    dialogType.value = 'add';
    resetRoleForm();
    dialogVisible.value = true;
  };

  // 编辑角色
  const handleEditRole = (row: Role) => {
    dialogType.value = 'edit';
    resetRoleForm();

    // 填充表单数据
    roleForm.id = row.id;
    roleForm.name = row.name;
    roleForm.code = row.code;
    roleForm.description = row.description;
    roleForm.status = row.status;

    dialogVisible.value = true;
  };

  // 重置角色表单
  const resetRoleForm = () => {
    roleForm.id = '';
    roleForm.name = '';
    roleForm.code = '';
    roleForm.description = '';
    roleForm.status = true;

    nextTick(() => {
      roleFormRef.value?.resetFields();
    });
  };

  // 提交角色表单
  const submitRoleForm = async () => {
    if (!roleFormRef.value) return;

    await roleFormRef.value.validate(async valid => {
      if (valid) {
        try {
          loading.value = true;

          // 模拟API调用
          await new Promise(resolve => setTimeout(resolve, 500));

          if (dialogType.value === 'add') {
            // 模拟添加角色
            const newRole: Role = {
              id: `role-${new Date().getTime()}`,
              name: roleForm.name,
              code: roleForm.code,
              description: roleForm.description,
              status: roleForm.status,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            };

            roleList.value.unshift(newRole);
            total.value++;

            ElMessage.success('新增角色成功');
          } else {
            // 模拟编辑角色
            const index = roleList.value.findIndex(role => role.id === roleForm.id);
            if (index !== -1) {
              roleList.value[index] = {
                ...roleList.value[index],
                name: roleForm.name,
                description: roleForm.description,
                status: roleForm.status,
                updated_at: new Date().toISOString(),
              };

              ElMessage.success('编辑角色成功');
            }
          }

          dialogVisible.value = false;
        } catch (error) {
          console.error('提交角色表单失败:', error);
          ElMessage.error('操作失败，请重试');
        } finally {
          loading.value = false;
        }
      }
    });
  };

  // 删除角色
  const handleDeleteRole = (row: Role) => {
    ElMessageBox.confirm('确定要删除该角色吗？删除后将无法恢复。', '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
      .then(async () => {
        try {
          loading.value = true;

          // 模拟API调用
          await new Promise(resolve => setTimeout(resolve, 500));

          // 从列表中移除
          roleList.value = roleList.value.filter(role => role.id !== row.id);
          total.value--;

          ElMessage.success('删除角色成功');
        } catch (error) {
          console.error('删除角色失败:', error);
          ElMessage.error('删除角色失败');
        } finally {
          loading.value = false;
        }
      })
      .catch(() => {
        // 取消删除
      });
  };

  // 切换角色状态
  const handleToggleStatus = async (row: Role) => {
    try {
      loading.value = true;

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500));

      // 更新状态
      const index = roleList.value.findIndex(role => role.id === row.id);
      if (index !== -1) {
        roleList.value[index].status = !roleList.value[index].status;

        ElMessage.success(`${roleList.value[index].status ? '启用' : '禁用'}角色成功`);
      }
    } catch (error) {
      console.error('切换角色状态失败:', error);
      ElMessage.error('操作失败，请重试');
    } finally {
      loading.value = false;
    }
  };

  // 分配权限
  const handleAssignPermissions = async (row: Role) => {
    currentRole.value = { ...row };

    try {
      loading.value = true;

      // 模拟获取权限树
      permissionTree.value = getMockPermissionTree();

      // 模拟获取角色已有权限
      await new Promise(resolve => setTimeout(resolve, 300));
      selectedPermissions.value = getRandomPermissionIds(permissionTree.value);

      permissionDialogVisible.value = true;
    } catch (error) {
      console.error('获取权限数据失败:', error);
      ElMessage.error('获取权限数据失败');
    } finally {
      loading.value = false;
    }
  };

  // 权限树过滤
  const filterPermissionNode = (value: string, data: any) => {
    if (!value) return true;
    return data.name.includes(value) || (data.code && data.code.includes(value));
  };

  // 监听过滤文本变化
  watch(permissionFilterText, val => {
    permissionTreeRef.value?.filter(val);
  });

  // 权限选中变更处理
  const handlePermissionCheck = (
    data: Permission,
    checked: { checkedKeys: string[]; checkedNodes: Permission[] },
  ) => {
    // 可以在这里处理联动逻辑
  };

  // 保存权限
  const savePermissions = async () => {
    try {
      loading.value = true;

      // 获取选中的权限ID
      const checkedKeys = permissionTreeRef.value?.getCheckedKeys() as string[];
      const halfCheckedKeys = permissionTreeRef.value?.getHalfCheckedKeys() as string[];
      const allSelectedKeys = [...checkedKeys, ...halfCheckedKeys];

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500));

      ElMessage.success(`已成功为角色 ${currentRole.value.name} 分配 ${checkedKeys.length} 个权限`);
      permissionDialogVisible.value = false;
    } catch (error) {
      console.error('保存权限失败:', error);
      ElMessage.error('保存权限失败');
    } finally {
      loading.value = false;
    }
  };

  // 查看角色用户
  const handleViewUsers = async (row: Role) => {
    currentRole.value = { ...row };
    userDialogVisible.value = true;

    await fetchRoleUsers();
  };

  // 获取角色用户列表
  const fetchRoleUsers = async () => {
    userLoading.value = true;
    try {
      // 模拟API请求
      await new Promise(resolve => setTimeout(resolve, 500));

      // 模拟用户数据
      const mockUsers = Array.from({ length: 30 }, (_, i) => {
        const date = new Date();
        date.setTime(date.getTime() - Math.random() * 30 * 24 * 3600 * 1000);

        return {
          id: `user-${i + 1}`,
          username: `user${i + 1}`,
          email: `user${i + 1}@example.com`,
          phone: `1398765${(1000 + i).toString().padStart(4, '0')}`,
          status: Math.random() > 0.1,
          lastLoginTime: date.toISOString(),
        };
      });

      // 分页
      const start = (userCurrentPage.value - 1) * userPageSize.value;
      const end = start + userPageSize.value;
      roleUserList.value = mockUsers.slice(start, end);
      userTotal.value = mockUsers.length;
    } catch (error) {
      console.error('获取角色用户列表失败:', error);
      ElMessage.error('获取角色用户列表失败');
    } finally {
      userLoading.value = false;
    }
  };

  // 用户列表分页处理
  const handleUserSizeChange = (val: number) => {
    userPageSize.value = val;
    fetchRoleUsers();
  };

  const handleUserCurrentChange = (val: number) => {
    userCurrentPage.value = val;
    fetchRoleUsers();
  };

  // 模拟权限树数据
  const getMockPermissionTree = (): Permission[] => {
    return [
      {
        id: 'system',
        name: '系统管理',
        code: 'system',
        children: [
          {
            id: 'user',
            name: '用户管理',
            code: 'user',
            children: [
              { id: 'user:view', name: '查看用户', code: 'user:view' },
              { id: 'user:create', name: '创建用户', code: 'user:create' },
              { id: 'user:edit', name: '编辑用户', code: 'user:edit' },
              { id: 'user:delete', name: '删除用户', code: 'user:delete' },
            ],
          },
          {
            id: 'role',
            name: '角色管理',
            code: 'role',
            children: [
              { id: 'role:view', name: '查看角色', code: 'role:view' },
              { id: 'role:create', name: '创建角色', code: 'role:create' },
              { id: 'role:edit', name: '编辑角色', code: 'role:edit' },
              { id: 'role:delete', name: '删除角色', code: 'role:delete' },
            ],
          },
          {
            id: 'permission',
            name: '权限管理',
            code: 'permission',
            children: [
              { id: 'permission:view', name: '查看权限', code: 'permission:view' },
              { id: 'permission:assign', name: '分配权限', code: 'permission:assign' },
            ],
          },
          {
            id: 'log',
            name: '日志管理',
            code: 'log',
            children: [
              { id: 'log:view', name: '查看日志', code: 'log:view' },
              { id: 'log:delete', name: '删除日志', code: 'log:delete' },
            ],
          },
        ],
      },
      {
        id: 'product',
        name: '产品管理',
        code: 'product',
        children: [
          { id: 'product:view', name: '查看产品', code: 'product:view' },
          { id: 'product:create', name: '创建产品', code: 'product:create' },
          { id: 'product:edit', name: '编辑产品', code: 'product:edit' },
          { id: 'product:delete', name: '删除产品', code: 'product:delete' },
        ],
      },
      {
        id: 'fuel-rate',
        name: '燃油费率管理',
        code: 'fuel-rate',
        children: [
          { id: 'fuel-rate:view', name: '查看费率', code: 'fuel-rate:view' },
          { id: 'fuel-rate:create', name: '创建费率', code: 'fuel-rate:create' },
          { id: 'fuel-rate:edit', name: '编辑费率', code: 'fuel-rate:edit' },
          { id: 'fuel-rate:delete', name: '删除费率', code: 'fuel-rate:delete' },
          { id: 'fuel-rate:trend', name: '查看趋势', code: 'fuel-rate:trend' },
        ],
      },
    ];
  };

  // 随机获取一些权限ID，用于模拟已分配权限
  const getRandomPermissionIds = (permissions: Permission[]): string[] => {
    const allIds: string[] = [];

    const extractIds = (items: Permission[]) => {
      for (const item of items) {
        if (!item.children || item.children.length === 0) {
          allIds.push(item.id);
        } else {
          extractIds(item.children);
        }
      }
    };

    extractIds(permissions);

    // 随机选择40%的权限
    const selectedCount = Math.floor(allIds.length * 0.4);
    const selectedIds: string[] = [];

    for (let i = 0; i < selectedCount; i++) {
      const randomIndex = Math.floor(Math.random() * allIds.length);
      selectedIds.push(allIds[randomIndex]);
      allIds.splice(randomIndex, 1);
    }

    return selectedIds;
  };

  onMounted(() => {
    fetchRoleList();
  });
</script>

<style scoped>
  .role-info {
    margin-bottom: var(--el-spacing-large);
    padding: var(--el-spacing-base);
    background-color: var(--el-fill-color-light);
    border-radius: var(--el-border-radius-base);

    h3 {
      color: var(--el-text-color-primary);
      margin-bottom: var(--el-spacing-small);
    }

    p {
      color: var(--el-text-color-secondary);
      margin: 0;
    }
  }

  .permission-tree-container {
    .permission-filter {
      margin-bottom: var(--el-spacing-base);
    }

    .permission-node {
      display: flex;
      align-items: center;
      gap: var(--el-spacing-base);

      .el-tag {
        margin-left: auto;
      }
    }
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: var(--el-spacing-base);
  }
</style>
