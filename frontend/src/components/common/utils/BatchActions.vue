<template>
  <div class="batch-actions-container">
    <el-popover
      v-model:visible="popoverVisible"
      placement="bottom-start"
      :width="300"
      trigger="click"
    >
      <template #reference>
        <el-button
          type="primary"
          :disabled="!hasSelected"
          @click="popoverVisible = true"
        >
          批量操作
          <el-icon class="el-icon--right"><arrow-down /></el-icon>
        </el-button>
      </template>

      <div class="batch-menu">
        <div class="menu-header">
          <span>已选择 {{ selectedCount }} 项</span>
          <el-button type="primary" link @click="handleClearSelection">
            清除选择
          </el-button>
        </div>

        <el-divider />

        <div class="menu-content">
          <el-scrollbar max-height="300px">
            <el-menu>
              <template v-for="group in actionGroups" :key="group.label">
                <el-menu-item-group :title="group.label">
                  <el-menu-item
                    v-for="action in group.actions"
                    :key="action.key"
                    @click="handleAction(action)"
                  >
                    <el-icon><component :is="action.icon" /></el-icon>
                    <span>{{ action.label }}</span>
                  </el-menu-item>
                </el-menu-item-group>
              </template>
            </el-menu>
          </el-scrollbar>
        </div>
      </div>
    </el-popover>

    <!-- 批量编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      :title="currentAction?.label || '批量编辑'"
      width="500px"
      destroy-on-close
    >
      <component
        :is="currentAction?.component"
        v-if="currentAction?.component"
        v-model="editForm"
        :selected-items="selectedItems"
      />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleConfirmEdit">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 确认对话框 -->
    <el-dialog
      v-model="confirmDialogVisible"
      :title="currentAction?.confirmTitle || '确认操作'"
      width="400px"
    >
      <p>{{ currentAction?.confirmMessage || '确定要执行此操作吗？' }}</p>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="confirmDialogVisible = false">取消</el-button>
          <el-button
            :type="currentAction?.confirmType || 'primary'"
            @click="handleConfirmAction"
          >
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { ArrowDown } from '@element-plus/icons-vue';

interface Action {
  key: string;
  label: string;
  icon?: string;
  component?: any;
  needConfirm?: boolean;
  confirmTitle?: string;
  confirmMessage?: string;
  confirmType?: 'primary' | 'success' | 'warning' | 'danger';
}

interface ActionGroup {
  label: string;
  actions: Action[];
}

interface Props {
  selectedItems: any[];
  actionGroups: ActionGroup[];
}

const props = withDefaults(defineProps<Props>(), {
  selectedItems: () => [],
  actionGroups: () => []
});

interface ActionEvent {
  type: string;
  items: any[];
  data?: any;
}

const emit = defineEmits<{
  (e: 'action', payload: ActionEvent): void;
  (e: 'clear-selection'): void;
}>();

const popoverVisible = ref(false);
const editDialogVisible = ref(false);
const confirmDialogVisible = ref(false);
const currentAction = ref<Action | null>(null);
const editForm = ref<Record<string, any>>({});

const selectedCount = computed(() => props.selectedItems.length);
const hasSelected = computed(() => selectedCount.value > 0);

// 处理操作选择
const handleAction = (action: Action) => {
  currentAction.value = action;
  popoverVisible.value = false;

  if (action.needConfirm) {
    confirmDialogVisible.value = true;
  } else if (action.component) {
    editDialogVisible.value = true;
  } else {
    emit('action', { type: action.key, items: props.selectedItems });
  }
};

// 处理确认操作
const handleConfirmAction = () => {
  if (!currentAction.value) return;
  confirmDialogVisible.value = false;
  emit('action', {
    type: currentAction.value.key,
    items: props.selectedItems
  });
};

// 处理确认编辑
const handleConfirmEdit = () => {
  if (!currentAction.value) return;
  editDialogVisible.value = false;
  emit('action', {
    type: currentAction.value.key,
    items: props.selectedItems,
    data: editForm.value
  });
};

// 清除选择
const handleClearSelection = () => {
  emit('clear-selection');
  popoverVisible.value = false;
};
</script>

<style scoped>
.batch-actions-container {
  display: inline-block;
}

.batch-menu {
  padding: 8px;
}

.menu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 8px;
}

.menu-content {
  margin-top: 8px;
}

:deep(.el-menu) {
  border-right: none;
}

:deep(.el-menu-item) {
  height: 40px;
  line-height: 40px;
}

:deep(.el-menu-item-group__title) {
  padding: 8px 16px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style> 