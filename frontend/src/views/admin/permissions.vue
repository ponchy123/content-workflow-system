<template>
  <div class="page-container">
    <el-card class="mb-base">
      <div class="page-header">
        <h1 class="page-title">权限管理</h1>
        <div class="flex gap-base">
          <el-button type="primary" @click="handleAddPermission">
            <el-icon><Plus /></el-icon>新增权限
          </el-button>
          <el-button @click="refreshPermissionList">
            <el-icon><Refresh /></el-icon>刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <el-card>
      <div class="flex items-center mb-base">
        <el-input
          v-model="filterText"
          placeholder="输入关键字进行过滤"
          class="mr-base"
          style="width: 300px"
          clearable
        />
        <el-radio-group v-model="viewMode" class="ml-auto">
          <el-radio-button value="tree">树形结构</el-radio-button>
          <el-radio-button value="list">列表结构</el-radio-button>
        </el-radio-group>
      </div>

      <div class="main-content">
        <el-card class="tree-card" v-if="viewMode === 'tree'">
          <template #header>
            <div class="card-header">
              <span>权限结构树</span>
            </div>
          </template>
          <el-tree
            ref="permissionTreeRef"
            :data="permissionTree"
            node-key="id"
            highlight-current
            :expand-on-click-node="false"
            :props="{ label: 'name', children: 'children' }"
            :filter-node-method="filterNode"
            @node-click="handleNodeClick"
          >
            <template #default="{ node, data }">
              <div class="custom-tree-node">
                <span class="node-label">{{ node.label }}</span>
                <span class="node-code" v-if="data.code">{{ data.code }}</span>
                <div class="node-actions">
                  <el-tooltip content="添加子权限" placement="top" v-if="!data.isButton">
                    <el-button
                      type="primary"
                      circle
                      size="small"
                      @click.stop="handleAddChild(data)"
                    >
                      <el-icon><Plus /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip content="编辑权限" placement="top">
                    <el-button
                      type="warning"
                      circle
                      size="small"
                      @click.stop="handleEditPermission(data)"
                    >
                      <el-icon><Edit /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip content="删除权限" placement="top">
                    <el-button
                      type="danger"
                      circle
                      size="small"
                      @click.stop="handleDeletePermission(data)"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </el-tooltip>
                </div>
              </div>
            </template>
          </el-tree>
        </el-card>

        <el-card class="detail-card" v-if="selectedPermission.id && viewMode === 'list'">
          <template #header>
            <div class="card-header">
              <span>权限详情</span>
              <el-button type="primary" link @click="handleEditPermission(selectedPermission)">
                <el-icon><Edit /></el-icon>编辑
              </el-button>
            </div>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="权限名称">{{
              selectedPermission.name
            }}</el-descriptions-item>
            <el-descriptions-item label="权限标识">{{
              selectedPermission.code
            }}</el-descriptions-item>
            <el-descriptions-item label="权限类型">
              <el-tag :type="selectedPermission.isButton ? 'danger' : 'primary'">
                {{ selectedPermission.isButton ? '按钮权限' : '菜单权限' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="权限描述">{{
              selectedPermission.description || '暂无描述'
            }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{
              formatDateTime(selectedPermission.created_at)
            }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{
              formatDateTime(selectedPermission.updated_at)
            }}</el-descriptions-item>
          </el-descriptions>

          <div class="roles-section" v-if="selectedPermission.id">
            <h3>拥有该权限的角色</h3>
            <el-table :data="permissionRoles" border stripe style="width: 100%">
              <el-table-column prop="name" label="角色名称" min-width="120" />
              <el-table-column prop="code" label="角色标识" min-width="120" />
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
            </el-table>
          </div>
        </el-card>
      </div>
    </el-card>

    <!-- 权限表单对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" destroy-on-close>
      <el-form
        ref="permissionFormRef"
        :model="permissionForm"
        :rules="permissionRules"
        label-width="100px"
      >
        <el-form-item label="父级权限" v-if="dialogType !== 'edit'">
          <el-cascader
            v-model="permissionForm.parentId"
            :options="cascaderOptions"
            :props="{
              checkStrictly: true,
              label: 'name',
              value: 'id',
              emitPath: false,
              disabled: (data: any) => Boolean(data.isButton),
            }"
            placeholder="请选择父级权限"
            clearable
          />
        </el-form-item>
        <el-form-item label="权限名称" prop="name">
          <el-input v-model="permissionForm.name" placeholder="请输入权限名称" />
        </el-form-item>
        <el-form-item label="权限标识" prop="code">
          <el-input
            v-model="permissionForm.code"
            placeholder="请输入权限标识"
            :disabled="dialogType === 'edit'"
          />
        </el-form-item>
        <el-form-item label="权限类型" prop="isButton">
          <el-radio-group v-model="permissionForm.isButton">
            <el-radio :value="false">菜单权限</el-radio>
            <el-radio :value="true">按钮权限</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="权限描述" prop="description">
          <el-input
            v-model="permissionForm.description"
            type="textarea"
            placeholder="请输入权限描述"
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="排序" prop="sort">
          <el-input-number v-model="permissionForm.sort" :min="0" :max="999" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitPermissionForm">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, watch, computed, onMounted, nextTick } from 'vue';
  import { ElMessage, ElMessageBox, ElTree } from 'element-plus';
  import { formatDateTime } from '@/utils/format';
  import { Plus, Edit, Delete, Refresh } from '@element-plus/icons-vue';
  import type { FormInstance, FormRules } from 'element-plus';

  // 权限数据接口
  interface Permission {
    id: string;
    name: string;
    code: string;
    parentId?: string;
    isButton: boolean;
    description?: string;
    sort: number;
    children?: Permission[];
    created_at: string;
    updated_at: string;
  }

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

  // 列表数据
  const loading = ref(false);
  const permissionTree = ref<Permission[]>([]);
  const permissionTreeRef = ref<InstanceType<typeof ElTree>>();
  const filterText = ref('');
  const selectedPermission = ref<Permission>({} as Permission);
  const permissionRoles = ref<Role[]>([]);
  const viewMode = ref<'tree' | 'list'>('tree');

  // 树形控件过滤
  const filterNode = (value: string, data: any) => {
    if (!value) return true;
    return data.name.includes(value) || (data.code && data.code.includes(value));
  };

  // 监听过滤文本变化
  watch(filterText, val => {
    permissionTreeRef.value?.filter(val);
  });

  // 获取权限列表
  const fetchPermissionList = async () => {
    loading.value = true;
    try {
      // 模拟后端API请求
      await new Promise(resolve => setTimeout(resolve, 500));

      // 模拟权限数据
      permissionTree.value = getMockPermissionTree();

      // 默认选中第一个权限
      if (permissionTree.value.length > 0) {
        nextTick(() => {
          handleNodeClick(permissionTree.value[0]);
        });
      }
    } catch (error) {
      console.error('获取权限列表失败:', error);
      ElMessage.error('获取权限列表失败');
    } finally {
      loading.value = false;
    }
  };

  // 刷新权限列表
  const refreshPermissionList = () => {
    fetchPermissionList();
  };

  // 点击树节点
  const handleNodeClick = (data: Permission) => {
    selectedPermission.value = data;
    fetchPermissionRoles(data.id);
  };

  // 获取拥有该权限的角色
  const fetchPermissionRoles = async (permissionId: string) => {
    try {
      // 模拟API请求
      await new Promise(resolve => setTimeout(resolve, 500));

      // 模拟角色数据
      const mockRoles = Array.from({ length: Math.floor(Math.random() * 5) + 1 }, (_, i) => {
        const date = new Date();
        date.setTime(date.getTime() - Math.random() * 90 * 24 * 3600 * 1000);

        const roleTypes = [
          { name: '超级管理员', code: 'admin' },
          { name: '系统管理员', code: 'system' },
          { name: '数据分析员', code: 'analyst' },
          { name: '运营人员', code: 'operator' },
          { name: '普通用户', code: 'user' },
        ];

        const roleType = roleTypes[i % roleTypes.length];

        return {
          id: `role-${i + 1}`,
          name: roleType.name,
          code: roleType.code,
          description: `${roleType.name}的权限描述`,
          status: Math.random() > 0.2,
          created_at: date.toISOString(),
          updated_at: date.toISOString(),
        };
      });

      permissionRoles.value = mockRoles;
    } catch (error) {
      console.error('获取权限角色失败:', error);
      ElMessage.error('获取权限角色失败');
    }
  };

  // 权限表单
  const dialogVisible = ref(false);
  const dialogType = ref<'add' | 'edit' | 'addChild'>('add');
  const permissionFormRef = ref<FormInstance>();
  const permissionForm = reactive({
    id: '',
    parentId: '',
    name: '',
    code: '',
    isButton: false,
    description: '',
    sort: 0,
  });

  // 表单验证规则
  const permissionRules = reactive<FormRules>({
    name: [
      { required: true, message: '请输入权限名称', trigger: 'blur' },
      { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' },
    ],
    code: [
      { required: true, message: '请输入权限标识', trigger: 'blur' },
      {
        pattern: /^[a-z][a-z0-9:]*$/,
        message: '权限标识只能包含小写字母、数字和冒号，且以字母开头',
        trigger: 'blur',
      },
    ],
    sort: [{ required: true, message: '请输入排序值', trigger: 'blur' }],
  });

  // 对话框标题
  const dialogTitle = computed(() => {
    switch (dialogType.value) {
      case 'add':
        return '新增权限';
      case 'edit':
        return '编辑权限';
      case 'addChild':
        return `新增 ${permissionForm.parentId ? getParentName(permissionForm.parentId) : ''} 的子权限`;
      default:
        return '';
    }
  });

  // 获取父级权限名称
  const getParentName = (parentId: string): string => {
    const findName = (permissions: Permission[]): string => {
      for (const permission of permissions) {
        if (permission.id === parentId) {
          return permission.name;
        }
        if (permission.children && permission.children.length > 0) {
          const name = findName(permission.children);
          if (name) return name;
        }
      }
      return '';
    };

    return findName(permissionTree.value);
  };

  // 级联选择器选项
  const cascaderOptions = computed(() => {
    return JSON.parse(JSON.stringify(permissionTree.value));
  });

  // 新增权限
  const handleAddPermission = () => {
    dialogType.value = 'add';
    resetPermissionForm();
    dialogVisible.value = true;
  };

  // 新增子权限
  const handleAddChild = (parentPermission: Permission) => {
    dialogType.value = 'addChild';
    resetPermissionForm();

    permissionForm.parentId = parentPermission.id;

    // 如果父级是按钮权限，不允许添加子权限
    if (parentPermission.isButton) {
      ElMessage.warning('按钮权限下不能添加子权限');
      return;
    }

    // 如果父级有标识，子级标识自动生成前缀
    if (parentPermission.code) {
      permissionForm.code = `${parentPermission.code}:`;
    }

    dialogVisible.value = true;
  };

  // 编辑权限
  const handleEditPermission = (permission: Permission) => {
    dialogType.value = 'edit';
    resetPermissionForm();

    // 填充表单数据
    permissionForm.id = permission.id;
    permissionForm.parentId = permission.parentId || '';
    permissionForm.name = permission.name;
    permissionForm.code = permission.code;
    permissionForm.isButton = permission.isButton;
    permissionForm.description = permission.description || '';
    permissionForm.sort = permission.sort;

    dialogVisible.value = true;
  };

  // 重置权限表单
  const resetPermissionForm = () => {
    permissionForm.id = '';
    permissionForm.parentId = '';
    permissionForm.name = '';
    permissionForm.code = '';
    permissionForm.isButton = false;
    permissionForm.description = '';
    permissionForm.sort = 0;

    nextTick(() => {
      permissionFormRef.value?.resetFields();
    });
  };

  // 提交权限表单
  const submitPermissionForm = async () => {
    if (!permissionFormRef.value) return;

    await permissionFormRef.value.validate(async valid => {
      if (valid) {
        try {
          loading.value = true;

          // 模拟API调用
          await new Promise(resolve => setTimeout(resolve, 500));

          if (dialogType.value === 'edit') {
            // 模拟编辑权限
            updatePermissionInTree(permissionTree.value, {
              id: permissionForm.id,
              name: permissionForm.name,
              code: permissionForm.code,
              parentId: permissionForm.parentId,
              isButton: permissionForm.isButton,
              description: permissionForm.description,
              sort: permissionForm.sort,
              created_at: selectedPermission.value.created_at,
              updated_at: new Date().toISOString(),
            });

            ElMessage.success('编辑权限成功');

            // 更新选中的权限
            if (selectedPermission.value.id === permissionForm.id) {
              selectedPermission.value = {
                ...selectedPermission.value,
                name: permissionForm.name,
                isButton: permissionForm.isButton,
                description: permissionForm.description,
                sort: permissionForm.sort,
                updated_at: new Date().toISOString(),
              };
            }
          } else {
            // 生成新权限
            const newPermission: Permission = {
              id: `permission-${new Date().getTime()}`,
              name: permissionForm.name,
              code: permissionForm.code,
              parentId: permissionForm.parentId || undefined,
              isButton: permissionForm.isButton,
              description: permissionForm.description,
              sort: permissionForm.sort,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            };

            // 添加到树中
            if (permissionForm.parentId) {
              addChildToParent(permissionTree.value, permissionForm.parentId, newPermission);
            } else {
              permissionTree.value.push(newPermission);
              // 根据排序值排序
              permissionTree.value.sort((a, b) => a.sort - b.sort);
            }

            ElMessage.success('新增权限成功');
          }

          dialogVisible.value = false;
        } catch (error) {
          console.error('提交权限表单失败:', error);
          ElMessage.error('操作失败，请重试');
        } finally {
          loading.value = false;
        }
      }
    });
  };

  // 更新树中的权限
  const updatePermissionInTree = (
    permissions: Permission[],
    updatedPermission: Permission,
  ): boolean => {
    for (let i = 0; i < permissions.length; i++) {
      if (permissions[i].id === updatedPermission.id) {
        permissions[i] = { ...permissions[i], ...updatedPermission };
        return true;
      }

      const children = permissions[i].children || [];
      if (children.length > 0) {
        if (updatePermissionInTree(children, updatedPermission)) {
          return true;
        }
      }
    }

    return false;
  };

  // 添加子权限到父权限
  const addChildToParent = (
    permissions: Permission[],
    parentId: string,
    newPermission: Permission,
  ): boolean => {
    for (let i = 0; i < permissions.length; i++) {
      if (permissions[i].id === parentId) {
        // 使用类型断言确保 children 是数组
        if (!permissions[i].children) {
          permissions[i].children = [];
        }

        (permissions[i].children as Permission[]).push(newPermission);
        // 根据排序值排序
        (permissions[i].children as Permission[]).sort((a, b) => a.sort - b.sort);
        return true;
      }

      // 使用类型断言处理 children
      const children = permissions[i].children || [];
      if (children.length > 0) {
        if (addChildToParent(children, parentId, newPermission)) {
          return true;
        }
      }
    }

    return false;
  };

  // 删除权限
  const handleDeletePermission = (permission: Permission) => {
    // 检查是否有子权限
    if (permission.children && permission.children.length > 0) {
      ElMessage.warning('该权限下有子权限，无法删除');
      return;
    }

    ElMessageBox.confirm(
      '确定要删除该权限吗？删除后将无法恢复，并可能影响已分配该权限的角色。',
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
      .then(async () => {
        try {
          loading.value = true;

          // 模拟API调用
          await new Promise(resolve => setTimeout(resolve, 500));

          // 从树中移除权限
          removePermissionFromTree(permissionTree.value, permission.id);

          // 如果删除的是当前选中的权限，清空选中
          if (selectedPermission.value.id === permission.id) {
            selectedPermission.value = {} as Permission;
            permissionRoles.value = [];
          }

          ElMessage.success('删除权限成功');
        } catch (error) {
          console.error('删除权限失败:', error);
          ElMessage.error('删除权限失败');
        } finally {
          loading.value = false;
        }
      })
      .catch(() => {
        // 取消删除
      });
  };

  // 从树中移除权限
  const removePermissionFromTree = (permissions: Permission[], permissionId: string): boolean => {
    for (let i = 0; i < permissions.length; i++) {
      if (permissions[i].id === permissionId) {
        permissions.splice(i, 1);
        return true;
      }

      const children = permissions[i].children || [];
      if (children.length > 0) {
        if (removePermissionFromTree(children, permissionId)) {
          return true;
        }
      }
    }

    return false;
  };

  // 模拟权限树数据
  const getMockPermissionTree = (): Permission[] => {
    const currentTime = new Date().toISOString();
    return [
      {
        id: 'system',
        name: '系统管理',
        code: 'system',
        isButton: false,
        sort: 1,
        created_at: currentTime,
        updated_at: currentTime,
        children: [
          {
            id: 'user',
            name: '用户管理',
            code: 'system:user',
            parentId: 'system',
            isButton: false,
            sort: 1,
            created_at: currentTime,
            updated_at: currentTime,
            children: [
              {
                id: 'user:view',
                name: '查看用户',
                code: 'system:user:view',
                parentId: 'user',
                isButton: true,
                sort: 1,
                created_at: currentTime,
                updated_at: currentTime,
              },
              {
                id: 'user:create',
                name: '创建用户',
                code: 'system:user:create',
                parentId: 'user',
                isButton: true,
                sort: 2,
                created_at: currentTime,
                updated_at: currentTime,
              },
              {
                id: 'user:edit',
                name: '编辑用户',
                code: 'system:user:edit',
                parentId: 'user',
                isButton: true,
                sort: 3,
                created_at: currentTime,
                updated_at: currentTime,
              },
              {
                id: 'user:delete',
                name: '删除用户',
                code: 'system:user:delete',
                parentId: 'user',
                isButton: true,
                sort: 4,
                created_at: currentTime,
                updated_at: currentTime,
              },
            ],
          },
          {
            id: 'role',
            name: '角色管理',
            code: 'system:role',
            parentId: 'system',
            isButton: false,
            sort: 2,
            created_at: currentTime,
            updated_at: currentTime,
            children: [
              {
                id: 'role:view',
                name: '查看角色',
                code: 'system:role:view',
                parentId: 'role',
                isButton: true,
                sort: 1,
                created_at: currentTime,
                updated_at: currentTime,
              },
              {
                id: 'role:create',
                name: '创建角色',
                code: 'system:role:create',
                parentId: 'role',
                isButton: true,
                sort: 2,
                created_at: currentTime,
                updated_at: currentTime,
              },
              {
                id: 'role:edit',
                name: '编辑角色',
                code: 'system:role:edit',
                parentId: 'role',
                isButton: true,
                sort: 3,
                created_at: currentTime,
                updated_at: currentTime,
              },
              {
                id: 'role:delete',
                name: '删除角色',
                code: 'system:role:delete',
                parentId: 'role',
                isButton: true,
                sort: 4,
                created_at: currentTime,
                updated_at: currentTime,
              },
            ],
          },
          {
            id: 'permission',
            name: '权限管理',
            code: 'system:permission',
            parentId: 'system',
            isButton: false,
            sort: 3,
            created_at: currentTime,
            updated_at: currentTime,
            children: [
              {
                id: 'permission:view',
                name: '查看权限',
                code: 'system:permission:view',
                parentId: 'permission',
                isButton: true,
                sort: 1,
                created_at: currentTime,
                updated_at: currentTime,
              },
              {
                id: 'permission:create',
                name: '创建权限',
                code: 'system:permission:create',
                parentId: 'permission',
                isButton: true,
                sort: 2,
                created_at: currentTime,
                updated_at: currentTime,
              },
              {
                id: 'permission:edit',
                name: '编辑权限',
                code: 'system:permission:edit',
                parentId: 'permission',
                isButton: true,
                sort: 3,
                created_at: currentTime,
                updated_at: currentTime,
              },
              {
                id: 'permission:delete',
                name: '删除权限',
                code: 'system:permission:delete',
                parentId: 'permission',
                isButton: true,
                sort: 4,
                created_at: currentTime,
                updated_at: currentTime,
              },
            ],
          },
          {
            id: 'log',
            name: '日志管理',
            code: 'system:log',
            parentId: 'system',
            isButton: false,
            sort: 4,
            created_at: currentTime,
            updated_at: currentTime,
            children: [
              {
                id: 'log:view',
                name: '查看日志',
                code: 'system:log:view',
                parentId: 'log',
                isButton: true,
                sort: 1,
                created_at: currentTime,
                updated_at: currentTime,
              },
              {
                id: 'log:delete',
                name: '删除日志',
                code: 'system:log:delete',
                parentId: 'log',
                isButton: true,
                sort: 2,
                created_at: currentTime,
                updated_at: currentTime,
              },
            ],
          },
        ],
      },
      {
        id: 'product',
        name: '产品管理',
        code: 'product',
        isButton: false,
        sort: 2,
        created_at: currentTime,
        updated_at: currentTime,
        children: [
          {
            id: 'product:view',
            name: '查看产品',
            code: 'product:view',
            parentId: 'product',
            isButton: true,
            sort: 1,
            created_at: currentTime,
            updated_at: currentTime,
          },
          {
            id: 'product:create',
            name: '创建产品',
            code: 'product:create',
            parentId: 'product',
            isButton: true,
            sort: 2,
            created_at: currentTime,
            updated_at: currentTime,
          },
          {
            id: 'product:edit',
            name: '编辑产品',
            code: 'product:edit',
            parentId: 'product',
            isButton: true,
            sort: 3,
            created_at: currentTime,
            updated_at: currentTime,
          },
          {
            id: 'product:delete',
            name: '删除产品',
            code: 'product:delete',
            parentId: 'product',
            isButton: true,
            sort: 4,
            created_at: currentTime,
            updated_at: currentTime,
          },
        ],
      },
      {
        id: 'fuel-rate',
        name: '燃油费率管理',
        code: 'fuel-rate',
        isButton: false,
        sort: 3,
        created_at: currentTime,
        updated_at: currentTime,
        children: [
          {
            id: 'fuel-rate:view',
            name: '查看费率',
            code: 'fuel-rate:view',
            parentId: 'fuel-rate',
            isButton: true,
            sort: 1,
            created_at: currentTime,
            updated_at: currentTime,
          },
          {
            id: 'fuel-rate:create',
            name: '创建费率',
            code: 'fuel-rate:create',
            parentId: 'fuel-rate',
            isButton: true,
            sort: 2,
            created_at: currentTime,
            updated_at: currentTime,
          },
          {
            id: 'fuel-rate:edit',
            name: '编辑费率',
            code: 'fuel-rate:edit',
            parentId: 'fuel-rate',
            isButton: true,
            sort: 3,
            created_at: currentTime,
            updated_at: currentTime,
          },
          {
            id: 'fuel-rate:delete',
            name: '删除费率',
            code: 'fuel-rate:delete',
            parentId: 'fuel-rate',
            isButton: true,
            sort: 4,
            created_at: currentTime,
            updated_at: currentTime,
          },
          {
            id: 'fuel-rate:trend',
            name: '查看趋势',
            code: 'fuel-rate:trend',
            parentId: 'fuel-rate',
            isButton: true,
            sort: 5,
            created_at: currentTime,
            updated_at: currentTime,
          },
        ],
      },
    ];
  };

  onMounted(() => {
    fetchPermissionList();
  });
</script>

<style scoped>
  .permission-info {
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

  .permission-node {
    display: flex;
    align-items: center;
    gap: var(--el-spacing-base);

    .el-tag {
      margin-left: auto;
    }
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: var(--el-spacing-base);
  }

  .page-container {
    padding: 20px;
  }

  .page-header-card {
    margin-bottom: 20px;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .action-buttons {
    display: flex;
    gap: 10px;
  }

  .main-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }

  .tree-card {
    height: 100%;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .custom-tree-node {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-right: 8px;
  }

  .node-label {
    font-size: 14px;
  }

  .node-code {
    color: #666;
    font-size: 12px;
    margin-left: 8px;
  }

  .node-actions {
    display: none;
    gap: 5px;
  }

  .custom-tree-node:hover .node-actions {
    display: flex;
  }

  .detail-card {
    height: 100%;
  }

  .roles-section {
    margin-top: 20px;
  }

  .roles-section h3 {
    margin-bottom: 15px;
    font-size: 16px;
    color: #409eff;
  }

  /* 响应式布局 */
  @media (max-width: 768px) {
    .page-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 10px;
    }

    .action-buttons {
      width: 100%;
      justify-content: flex-end;
    }

    .main-content {
      grid-template-columns: 1fr;
    }
  }
</style>
