<template>
  <div class="config-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ title }}</span>
          <el-button type="primary" @click="handleAddConfig">
            <el-icon><plus /></el-icon>添加配置
          </el-button>
        </div>
      </template>

      <!-- 配置列表 -->
      <el-table :data="configList" border stripe>
        <el-table-column prop="key" label="配置项" min-width="150" />
        <el-table-column prop="value" label="配置值" min-width="200">
          <template #default="{ row }">
            <template v-if="row.editing">
              <component
                :is="getEditorComponent(row.type)"
                v-model="row.editValue"
                v-bind="row.editorProps || {}"
              />
            </template>
            <template v-else>
              <component
                :is="getDisplayComponent(row.type)"
                :value="row.value"
                v-bind="row.displayProps || {}"
              />
            </template>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status ? 'success' : 'danger'">
              {{ row.status ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <template v-if="row.editing">
              <el-button type="primary" link @click="handleSaveConfig(row)">
                <el-icon><check /></el-icon>保存
              </el-button>
              <el-button type="info" link @click="handleCancelEdit(row)">
                <el-icon><close /></el-icon>取消
              </el-button>
            </template>
            <template v-else>
              <el-button type="primary" link @click="handleEditConfig(row)">
                <el-icon><edit /></el-icon>编辑
              </el-button>
              <el-button
                :type="row.status ? 'danger' : 'success'"
                link
                @click="handleToggleStatus(row)"
              >
                <el-icon>
                  <component :is="row.status ? 'close' : 'check'" />
                </el-icon>
                {{ row.status ? '禁用' : '启用' }}
              </el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑配置对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑配置' : '添加配置'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="configForm"
        :rules="configRules"
        label-width="100px"
      >
        <el-form-item label="配置项" prop="key">
          <el-input
            v-model="configForm.key"
            :disabled="isEdit"
            placeholder="请输入配置项"
          />
        </el-form-item>
        <el-form-item label="配置类型" prop="type">
          <el-select v-model="configForm.type" placeholder="请选择配置类型">
            <el-option
              v-for="type in configTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="配置值" prop="value">
          <component
            :is="getEditorComponent(configForm.type)"
            v-model="configForm.value"
            v-bind="getEditorProps(configForm.type)"
          />
        </el-form-item>
        <el-form-item label="说明" prop="description">
          <el-input
            v-model="configForm.description"
            type="textarea"
            placeholder="请输入配置说明"
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-switch v-model="configForm.status" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmitConfig">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Plus, Edit, Check, Close } from '@element-plus/icons-vue';
import type { FormInstance, FormRules } from 'element-plus';
import type { ConfigItem, ConfigTypeOption } from '@/types/config';

interface Props {
  title?: string;
  configTypes?: ConfigTypeOption[];
}

const props = withDefaults(defineProps<Props>(), {
  title: '配置管理',
  configTypes: () => [
    { label: '文本', value: 'text' },
    { label: '数字', value: 'number' },
    { label: '开关', value: 'switch' },
    { label: '选择器', value: 'select' },
    { label: '日期', value: 'date' },
    { label: '时间', value: 'time' },
    { label: 'JSON', value: 'json' }
  ]
});

const emit = defineEmits<{
  (e: 'update', config: ConfigItem): void;
  (e: 'save', config: Omit<ConfigItem, 'id'>): void;
  (e: 'delete', id: string): void;
}>();

const configList = ref<ConfigItem[]>([]);
const dialogVisible = ref(false);
const isEdit = ref(false);
const formRef = ref<FormInstance>();

const configForm = ref<Omit<ConfigItem, 'id'>>({
  key: '',
  type: 'text',
  value: '',
  description: '',
  status: true
});

const configRules: FormRules = {
  key: [
    { required: true, message: '请输入配置项', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '配置项只能包含字母、数字和下划线，且必须以字母开头', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择配置类型', trigger: 'change' }
  ],
  value: [
    { required: true, message: '请输入配置值', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入配置说明', trigger: 'blur' }
  ]
};

// 获取编辑器组件
const getEditorComponent = (type: ConfigItem['type']) => {
  const componentMap: Record<ConfigItem['type'], string> = {
    text: 'el-input',
    number: 'el-input-number',
    switch: 'el-switch',
    select: 'el-select',
    date: 'el-date-picker',
    time: 'el-time-picker',
    json: 'el-input'
  };
  return componentMap[type] || 'el-input';
};

// 获取显示组件
const getDisplayComponent = (type: ConfigItem['type']) => {
  const componentMap: Record<ConfigItem['type'], string> = {
    text: 'span',
    number: 'span',
    switch: 'el-tag',
    select: 'el-tag',
    date: 'span',
    time: 'span',
    json: 'pre'
  };
  return componentMap[type] || 'span';
};

// 获取编辑器属性
const getEditorProps = (type: ConfigItem['type']) => {
  const propsMap: Record<ConfigItem['type'], Record<string, any>> = {
    text: { type: 'text', placeholder: '请输入' },
    number: { min: 0, controls: true },
    switch: { activeText: '是', inactiveText: '否' },
    select: { placeholder: '请选择' },
    date: { type: 'date', placeholder: '请选择日期' },
    time: { placeholder: '请选择时间' },
    json: { type: 'textarea', rows: 4, placeholder: '请输入JSON格式的配置值' }
  };
  return propsMap[type] || {};
};

// 处理添加配置
const handleAddConfig = () => {
  isEdit.value = false;
  configForm.value = {
    key: '',
    type: 'text',
    value: '',
    description: '',
    status: true
  };
  dialogVisible.value = true;
};

// 处理编辑配置
const handleEditConfig = (row: ConfigItem) => {
  row.editing = true;
  row.editValue = row.value;
};

// 处理保存配置
const handleSaveConfig = async (row: ConfigItem) => {
  try {
    await emit('save', {
      ...row,
      value: row.editValue
    });
    row.value = row.editValue;
    row.editing = false;
  } catch (error) {
    console.error('保存配置失败:', error);
  }
};

// 处理取消编辑
const handleCancelEdit = (row: ConfigItem) => {
  row.editing = false;
  row.editValue = row.value;
};

// 处理切换状态
const handleToggleStatus = async (row: ConfigItem) => {
  try {
    await emit('update', {
      ...row,
      status: !row.status
    });
    row.status = !row.status;
  } catch (error) {
    console.error('更新状态失败:', error);
  }
};

// 处理提交配置
const handleSubmitConfig = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await emit('save', configForm.value);
        dialogVisible.value = false;
        if (!isEdit.value) {
          configList.value.push({
            ...configForm.value,
            id: '', // 临时ID，实际应该由后端生成
            editing: false
          });
        }
      } catch (error) {
        console.error('保存配置失败:', error);
      }
    }
  });
};
</script>

<style scoped>
.config-manager {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.json-editor) {
  height: 100px;
  font-family: monospace;
}
</style> 