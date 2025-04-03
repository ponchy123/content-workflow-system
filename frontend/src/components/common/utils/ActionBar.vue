<template>
  <div class="action-bar" :class="{ 'is-vertical': vertical }">
    <!-- 主要操作按钮 -->
    <div class="action-bar__primary">
      <template v-for="action in primaryActions" :key="action.key">
        <el-button
          v-if="checkPermission(action.permission)"
          v-bind="getButtonProps(action)"
          @click="handleAction(action)"
        >
          <el-icon v-if="action.icon" class="action-icon">
            <component :is="action.icon" />
          </el-icon>
          {{ action.label }}
        </el-button>
      </template>
    </div>

    <!-- 次要操作按钮 -->
    <div class="action-bar__secondary">
      <template v-for="action in secondaryActions" :key="action.key">
        <el-button
          v-if="checkPermission(action.permission)"
          v-bind="getButtonProps(action)"
          @click="handleAction(action)"
        >
          <el-icon v-if="action.icon" class="action-icon">
            <component :is="action.icon" />
          </el-icon>
          {{ action.label }}
        </el-button>
      </template>

      <!-- 更多操作下拉菜单 -->
      <el-dropdown
        v-if="moreActions.length && hasMoreActionsPermission"
        @command="handleMoreAction"
      >
        <el-button>
          更多操作
          <el-icon class="el-icon--right">
            <arrow-down />
          </el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item
              v-for="action in moreActions"
              :key="action.key"
              :command="action"
              :disabled="action.disabled"
              v-show="checkPermission(action.permission)"
            >
              <el-icon v-if="action.icon">
                <component :is="action.icon" />
              </el-icon>
              {{ action.label }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import { ArrowDown } from '@element-plus/icons-vue';
  import { usePermission } from '@/composables/usePermission';

  interface Action {
    key: string;
    label: string;
    type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'text' | 'default';
    icon?: string;
    permission?: string | string[];
    disabled?: boolean;
    loading?: boolean;
    props?: Record<string, any>;
    handler?: () => void;
  }

  interface Props {
    primaryActions?: Action[];
    secondaryActions?: Action[];
    moreActions?: Action[];
    vertical?: boolean;
    size?: 'large' | 'default' | 'small';
  }

  const props = withDefaults(defineProps<Props>(), {
    primaryActions: () => [],
    secondaryActions: () => [],
    moreActions: () => [],
    vertical: false,
    size: 'default',
  });

  const emit = defineEmits<{
    (e: 'action', key: string): void;
  }>();

  const { checkPermission } = usePermission();

  // 检查是否有任何可显示的更多操作
  const hasMoreActionsPermission = computed(() => {
    return props.moreActions.some(action => checkPermission(action.permission));
  });

  // 获取按钮属性
  const getButtonProps = (action: Action) => {
    return {
      type: action.type || 'default',
      size: props.size,
      disabled: action.disabled,
      loading: action.loading,
      ...action.props,
    };
  };

  // 处理按钮点击
  const handleAction = (action: Action) => {
    if (action.handler) {
      action.handler();
    } else {
      emit('action', action.key);
    }
  };

  // 处理更多操作
  const handleMoreAction = (action: Action) => {
    handleAction(action);
  };
</script>

<style>
  .action-bar {
    display: flex;
    gap: var(--spacing-md);
    align-items: center;
  }

  .action-bar.is-vertical {
    flex-direction: column;
    align-items: stretch;
  }

  .action-bar__primary,
  .action-bar__secondary {
    display: flex;
    gap: var(--spacing-sm);
    align-items: center;
  }

  .action-bar.is-vertical .action-bar__primary,
  .action-bar.is-vertical .action-bar__secondary {
    flex-direction: column;
    align-items: stretch;
  }

  .action-icon {
    margin-right: var(--spacing-xs);
  }

  /* 响应式调整 */
  @media screen and (max-width: 768px) {
    .action-bar {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-sm);
    }

    .action-bar__primary,
    .action-bar__secondary {
      flex-wrap: wrap;
    }

    .action-bar__primary .el-button,
    .action-bar__secondary .el-button {
      flex: 1;
      min-width: 120px;
    }
  }

  /* 暗色主题 */
  .dark .action-bar {
    --el-button-bg-color: var(--el-bg-color-overlay);
    --el-button-border-color: var(--el-border-color-darker);
    --el-button-hover-bg-color: var(--el-color-primary-light-3);
    --el-button-hover-border-color: var(--el-color-primary);
  }
</style>
