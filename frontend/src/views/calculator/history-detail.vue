<template>
  <div class="history-detail-container">
    <el-page-header @back="goBack">
      <template #content>历史记录详情</template>
    </el-page-header>

    <div class="detail-content" v-loading="historyStore.loading">
      <template v-if="historyStore.currentDetail">
        <el-card class="detail-card">
          <template #header>
            <div class="card-header">
              <h3>基本信息</h3>
              <el-button-group>
                <el-button type="primary" @click="handleRecalculate"> 重新计算 </el-button>
                <el-button type="primary" @click="handleExport"> 导出详情 </el-button>
              </el-button-group>
            </div>
          </template>

          <el-descriptions :column="2" border>
            <el-descriptions-item label="计算时间">
              {{ formatDate(historyStore.currentDetail.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="计算类型">
              <el-tag :type="getTypeTagType(historyStore.currentDetail.type)">
                {{ getTypeLabel(historyStore.currentDetail.type) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="操作用户">
              {{ historyStore.currentDetail.user.username }}
            </el-descriptions-item>
            <el-descriptions-item label="用户邮箱">
              {{ historyStore.currentDetail.user.email }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- ... 其余模板代码保持不变 ... -->
      </template>

      <el-empty v-else description="未找到记录" />
    </div>
  </div>
</template>

<script setup lang="ts">
  import { onMounted } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import { ElMessage } from 'element-plus';
  import { useHistoryStore } from '@/stores/calculator/history';
  import { useCalculatorStore } from '@/stores/calculator';
  import { formatDate } from '@/utils/format/date';
  import { formatCurrency } from '@/utils/format';
  import type { CalculationHistory } from '@/types/calculator';

  const route = useRoute();
  const router = useRouter();
  const historyStore = useHistoryStore();
  const calculatorStore = useCalculatorStore();

  // 获取类型标签样式
  const getTypeTagType = (type: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' => {
    const types: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
      single: 'primary',
      batch: 'success',
      comparison: 'warning',
    };
    return types[type] || 'info';
  };

  // 获取类型标签文本
  const getTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      single: '单次计算',
      batch: '批量计算',
      comparison: '产品比较',
    };
    return labels[type] || type;
  };

  // 返回上一页
  const goBack = () => {
    router.back();
  };

  // 重新计算
  const handleRecalculate = async () => {
    if (!historyStore.currentDetail) return;

    await calculatorStore.calculate(historyStore.currentDetail.request);
    router.push('/calculator');
  };

  // 导出详情
  const handleExport = () => {
    if (!historyStore.currentDetail) return;
    historyStore.exportDetail(historyStore.currentDetail.id);
  };

  // 初始化
  onMounted(async () => {
    const id = route.params.id as string;
    await historyStore.fetchHistoryDetail(id);
  });
</script>

<style scoped>
  .history-detail-container {
    padding: 20px;
  }

  .detail-card {
    margin-bottom: 20px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .total-charge {
    color: #f56c6c;
    font-size: 16px;
    font-weight: bold;
  }
</style>
