<template>
  <div class="language-switch">
    <!-- 下拉菜单 -->
    <el-dropdown v-if="mode === 'dropdown'" trigger="click" @command="handleCommand">
      <el-button :type="buttonType" :size="size">
        <template v-if="showIcon">
          <el-icon class="language-switch__icon">
            <component :is="currentLanguageIcon" />
          </el-icon>
        </template>
        {{ currentLanguageLabel }}
        <el-icon class="el-icon--right">
          <arrow-down />
        </el-icon>
      </el-button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item
            v-for="lang in languages"
            :key="lang.value"
            :command="lang.value"
            :disabled="lang.value === currentLanguage"
          >
            <template v-if="showIcon">
              <el-icon class="language-switch__icon">
                <component :is="lang.icon" />
              </el-icon>
            </template>
            {{ lang.label }}
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>

    <!-- 单选按钮组 -->
    <el-radio-group v-else v-model="currentLanguage" :size="size" @change="(val: any) => handleChange(val as 'zh-CN' | 'en-US')">
      <el-radio-button v-for="lang in languages" :key="lang.value" :value="lang.value">
        <template v-if="showIcon">
          <el-icon class="language-switch__icon">
            <component :is="lang.icon" />
          </el-icon>
        </template>
        {{ lang.label }}
      </el-radio-button>
    </el-radio-group>
  </div>
</template>

<script setup lang="ts">
  import { computed, ref } from 'vue';
  import { ArrowDown } from '@element-plus/icons-vue';
  import { useI18n } from '@/composables/useI18n';

  interface Language {
    label: string;
    value: 'zh-CN' | 'en-US';
    icon?: string;
  }

  interface Props {
    mode?: 'dropdown' | 'radio';
    buttonType?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'text' | '';
    size?: 'large' | 'default' | 'small';
    showIcon?: boolean;
    languages?: Language[];
  }

  const props = withDefaults(defineProps<Props>(), {
    mode: 'dropdown',
    buttonType: '',
    size: 'default',
    showIcon: true,
    languages: () => [
      { label: '简体中文', value: 'zh-CN', icon: 'Flag' },
      { label: 'English', value: 'en-US', icon: 'Flag' },
    ],
  });

  const { currentLanguage, setLanguage } = useI18n();

  // 当前语言标签
  const currentLanguageLabel = computed(() => {
    const lang = props.languages.find(lang => lang.value === currentLanguage.value);
    return lang?.label || '';
  });

  // 当前语言图标
  const currentLanguageIcon = computed(() => {
    const lang = props.languages.find(lang => lang.value === currentLanguage.value);
    return lang?.icon;
  });

  // 处理下拉菜单选择
  const handleCommand = (command: 'zh-CN' | 'en-US') => {
    setLanguage(command);
  };

  // 处理单选按钮组变化
  const handleChange = (value: 'zh-CN' | 'en-US') => {
    setLanguage(value);
  };
</script>

<style scoped>
  .language-switch {
    display: inline-block;
  }

  .language-switch__icon {
    margin-right: var(--spacing-xs);
  }

  /* 暗色主题 */
  .dark .language-switch .el-dropdown-menu {
    background-color: var(--el-bg-color-overlay);
    border-color: var(--el-border-color-darker);
  }
</style>
