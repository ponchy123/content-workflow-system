<template>
  <div class="history-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>计算历史</h2>
          <div class="header-actions">
            <el-button-group>
              <el-button type="danger" @click="handleClearHistory">
                <el-icon><delete /></el-icon>
                清空历史
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>

      <calculation-history
        ref="historyComponent"
        :loading="historyStore.loading"
        :data="historyStore.histories"
        @export="handleExport"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
  import { ref } from 'vue';
  import { Delete } from '@element-plus/icons-vue';
  import { ElMessageBox, ElMessage } from 'element-plus';
  import { useHistoryStore } from '@/stores/calculator/history';
  import { CalculationHistory } from '@/components/calculator';

  const historyStore = useHistoryStore();
  const historyComponent = ref<InstanceType<typeof CalculationHistory>>();

  // 处理导出
  const handleExport = () => {
    historyStore.exportHistory();
  };

  // 处理清空历史
  const handleClearHistory = async () => {
    try {
      await ElMessageBox.confirm('确定要清空所有历史记录吗？', '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      });

      await historyStore.clearHistory();
      ElMessage.success('历史记录已清空');
    } catch (error) {
      if (error !== 'cancel') {
        console.error('清空历史失败:', error);
        ElMessage.error('清空历史失败');
      }
    }
  };
</script>

<style>
  .history-container {
    padding: var(--spacing-md);
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .card-header h2 {
    margin: 0;
    font-size: var(--font-size-large);
    color: var(--text-color-primary);
  }

  .header-actions {
    display: flex;
    gap: var(--spacing-sm);
  }
</style>
