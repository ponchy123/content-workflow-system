<template>
  <div class="config-value-editor">
    <!-- 语言选择器 -->
    <template v-if="isLanguageSelect">
      <el-select v-model="localValue" placeholder="请选择系统语言" @change="handleChange">
        <el-option
          v-for="lang in availableLanguages"
          :key="lang.code"
          :label="lang.name"
          :value="lang.code"
        />
      </el-select>
    </template>

    <!-- 主题选择器 -->
    <template v-else-if="isThemeSelect">
      <div class="theme-selector">
        <el-radio-group v-model="localTheme.mode" @change="handleThemeChange">
          <el-radio-button value="light">亮色</el-radio-button>
          <el-radio-button value="dark">暗色</el-radio-button>
        </el-radio-group>

        <el-form class="theme-form" label-width="100px">
          <el-form-item label="主色调">
            <el-color-picker
              v-model="localTheme.primary_color"
              show-alpha
              @change="handleThemeChange"
            />
          </el-form-item>
          <el-form-item label="成功色">
            <el-color-picker
              v-model="localTheme.success_color"
              show-alpha
              @change="handleThemeChange"
            />
          </el-form-item>
          <el-form-item label="警告色">
            <el-color-picker
              v-model="localTheme.warning_color"
              show-alpha
              @change="handleThemeChange"
            />
          </el-form-item>
          <el-form-item label="危险色">
            <el-color-picker
              v-model="localTheme.danger_color"
              show-alpha
              @change="handleThemeChange"
            />
          </el-form-item>
          <el-form-item label="信息色">
            <el-color-picker
              v-model="localTheme.info_color"
              show-alpha
              @change="handleThemeChange"
            />
          </el-form-item>
          <el-form-item label="圆角大小">
            <el-input-number
              v-model="localTheme.border_radius_value"
              :min="0"
              :max="20"
              @change="handleBorderRadiusChange"
            />
          </el-form-item>
        </el-form>

        <div class="theme-preview">
          <h4>主题预览</h4>
          <div class="preview-buttons" :style="previewStyle">
            <el-button type="primary">主要按钮</el-button>
            <el-button type="success">成功按钮</el-button>
            <el-button type="warning">警告按钮</el-button>
            <el-button type="danger">危险按钮</el-button>
            <el-button type="info">信息按钮</el-button>
          </div>
        </div>
      </div>
    </template>

    <!-- 文本类型 -->
    <el-input
      v-else-if="type === 'string'"
      v-model="localValue"
      :placeholder="getPlaceholder"
      :maxlength="validationRules?.max_length"
      show-word-limit
      @change="handleChange"
    />

    <!-- 数字类型 -->
    <el-input-number
      v-else-if="type === 'number'"
      v-model="localValue"
      :min="validationRules?.min"
      :max="validationRules?.max"
      :step="1"
      @change="handleChange"
    />

    <!-- 布尔类型 -->
    <el-switch v-else-if="type === 'boolean'" v-model="localValue" @change="handleChange" />

    <!-- 邮箱类型 -->
    <el-input
      v-else-if="type === 'email'"
      v-model="localValue"
      type="email"
      placeholder="请输入邮箱地址"
      @change="handleChange"
    />

    <!-- 数组类型 -->
    <div v-else-if="type === 'array'" class="array-editor">
      <div v-for="(item, index) in localValue" :key="index" class="array-item">
        <el-input
          v-model="localValue[index]"
          :placeholder="`项目 ${index + 1}`"
          @change="handleChange"
        >
          <template #append>
            <el-button @click="removeArrayItem(index)">
              <el-icon><delete /></el-icon>
            </el-button>
          </template>
        </el-input>
      </div>
      <el-button
        v-if="!validationRules?.max_items || localValue.length < validationRules.max_items"
        type="primary"
        plain
        @click="addArrayItem"
      >
        添加项目
      </el-button>
    </div>

    <!-- JSON类型 -->
    <div v-else-if="type === 'json'" class="json-editor">
      <el-input
        v-model="jsonString"
        type="textarea"
        :rows="5"
        placeholder="请输入有效的JSON"
        @change="handleJsonChange"
      />
      <div v-if="jsonError" class="json-error">
        {{ jsonError }}
      </div>
    </div>

    <!-- 默认文本类型 -->
    <el-input v-else v-model="localValue" placeholder="请输入值" @change="handleChange" />
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, watch, onMounted } from 'vue';
  import { Delete } from '@element-plus/icons-vue';

  interface Language {
    code: string;
    name: string;
  }

  interface FormItemRule {
    type?: string;
    pattern?: string;
    max_length?: number;
    min?: number;
    max?: number;
    max_items?: number;
  }

  interface ThemeConfig {
    mode: string;
    primary_color: string;
    success_color: string;
    warning_color: string;
    danger_color: string;
    info_color: string;
    border_radius: string;
    border_radius_value?: number;
    font_family: string;
  }

  const props = defineProps<{
    modelValue: any;
    type: string;
    mode?: 'edit' | 'display';
    options?: Record<string, any>;
    rules?: FormItemRule;
  }>();

  const emit = defineEmits(['update:modelValue']);

  // 本地值
  const localValue = ref(props.modelValue);

  // JSON编辑器相关
  const jsonString = ref('');
  const jsonError = ref('');

  // 验证规则
  const validationRules = computed(() => props.rules || {});

  // 根据mode决定是否显示编辑控件
  const isEditMode = computed(() => props.mode !== 'display');

  // 计算属性：占位符
  const getPlaceholder = computed(() => {
    switch (props.type) {
      case 'string':
        return '请输入文本';
      case 'number':
        return '请输入数字';
      case 'email':
        return '请输入邮箱地址';
      case 'array':
        return '请添加项目';
      case 'json':
        return '请输入JSON';
      default:
        return '请输入值';
    }
  });

  // 计算属性：是否为语言选择
  const isLanguageSelect = computed(() => {
    return props.rules?.type === 'string' && props.rules?.pattern === '^[a-z]{2}_[A-Z]{2}$';
  });

  // 计算属性：是否为主题选择
  const isThemeSelect = computed(() => {
    return props.rules?.type === 'json' && props.modelValue?.mode !== undefined;
  });

  // 获取可用语言列表
  const availableLanguages = ref<Language[]>([]);
  const fetchAvailableLanguages = async () => {
    try {
      const response = await fetch('/api/system-configs/key/available_languages');
      const data = await response.json();
      availableLanguages.value = data.value;
    } catch (error) {
      console.error('获取可用语言列表失败:', error);
    }
  };

  // 主题相关
  const localTheme = ref<ThemeConfig>({
    mode: 'light',
    primary_color: '#409EFF',
    success_color: '#67C23A',
    warning_color: '#E6A23C',
    danger_color: '#F56C6C',
    info_color: '#909399',
    border_radius: '4px',
    border_radius_value: 4,
    font_family: 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial',
  });

  // 计算属性：预览样式
  const previewStyle = computed(() => {
    return {
      '--el-color-primary': localTheme.value.primary_color,
      '--el-color-success': localTheme.value.success_color,
      '--el-color-warning': localTheme.value.warning_color,
      '--el-color-danger': localTheme.value.danger_color,
      '--el-color-info': localTheme.value.info_color,
      '--el-border-radius-base': localTheme.value.border_radius,
      'background-color': localTheme.value.mode === 'dark' ? '#1f1f1f' : '#ffffff',
      padding: '20px',
      'border-radius': '8px',
    };
  });

  // 监听值变化
  watch(
    () => props.modelValue,
    newVal => {
      if (props.type === 'json') {
        try {
          jsonString.value = JSON.stringify(newVal, null, 2);
          jsonError.value = '';
        } catch (error) {
          jsonError.value = '无效的JSON格式';
        }
      } else {
        localValue.value = newVal;
      }
      if (isThemeSelect.value && newVal) {
        localTheme.value = { ...newVal };
      }
    },
    { immediate: true },
  );

  // 处理值变化
  const handleChange = () => {
    emit('update:modelValue', localValue.value);
  };

  // 处理JSON变化
  const handleJsonChange = () => {
    try {
      const parsed = JSON.parse(jsonString.value);
      jsonError.value = '';
      emit('update:modelValue', parsed);
    } catch (error) {
      jsonError.value = '无效的JSON格式';
    }
  };

  // 数组操作
  const addArrayItem = () => {
    if (!Array.isArray(localValue.value)) {
      localValue.value = [];
    }
    localValue.value.push('');
    handleChange();
  };

  const removeArrayItem = (index: number) => {
    localValue.value.splice(index, 1);
    handleChange();
  };

  // 处理主题变化
  const handleThemeChange = () => {
    emit('update:modelValue', { ...localTheme.value });
  };

  // 处理边框圆角变化
  const handleBorderRadiusChange = (value: number | undefined) => {
    if (value !== undefined) {
      localTheme.value.border_radius = `${value}px`;
      localTheme.value.border_radius_value = value;
      handleThemeChange();
    }
  };

  // 在组件挂载时获取可用语言列表
  onMounted(() => {
    if (isLanguageSelect.value) {
      fetchAvailableLanguages();
    }
  });

  // 初始化默认值
  if (localValue.value === null) {
    switch (props.type) {
      case 'string':
      case 'email':
        localValue.value = '';
        break;
      case 'number':
        localValue.value = 0;
        break;
      case 'boolean':
        localValue.value = false;
        break;
      case 'array':
        localValue.value = [];
        break;
      case 'json':
        localValue.value = {};
        jsonString.value = '{}';
        break;
    }
  }
</script>

<style scoped>
  .config-value-editor {
    width: 100%;
  }

  .array-editor {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .array-item {
    display: flex;
    gap: 10px;
  }

  .json-editor {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .json-error {
    color: #f56c6c;
    font-size: 12px;
  }

  .theme-selector {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .theme-form {
    margin-top: 20px;
  }

  .theme-preview {
    margin-top: 20px;
    border: 1px solid var(--el-border-color);
    border-radius: 8px;
    overflow: hidden;
  }

  .theme-preview h4 {
    margin: 0;
    padding: 10px;
    background-color: var(--el-color-primary-light-9);
    border-bottom: 1px solid var(--el-border-color);
  }

  .preview-buttons {
    padding: 20px;
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }
</style>
