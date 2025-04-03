<template>
  <div class="fuel-rate-table">
    <data-table
      :data="data"
      :loading="loading"
      :columns="columns"
      :pagination-config="{
        currentPage,
        pageSize,
        total,
        pageSizes: [10, 20, 50, 100],
      }"
      border
      @update:pagination="handlePaginationChange"
    >
      <template #rate="{ row }">
        {{ formatPercent(row.rate) }}
      </template>
      <template #effective_date="{ row }">
        {{ formatDateTime(row.effective_date, 'YYYY-MM-DD') }}
      </template>
      <template #expiry_date="{ row }">
        {{ row.expiry_date ? formatDateTime(row.expiry_date, 'YYYY-MM-DD') : '永久有效' }}
      </template>
      <template #is_active="{ row }">
        <el-tag :type="row.is_active ? 'success' : 'danger'">
          {{ row.is_active ? '启用' : '禁用' }}
        </el-tag>
      </template>
      <template #created_at="{ row }">
        {{ formatDateTime(row.created_at) }}
      </template>
      <template #actions="{ row }">
        <el-button
          type="primary"
          link
          @click="handleEdit(row)"
          v-if="hasPermission('fuel_rate:edit')"
        >
          编辑
        </el-button>
        <el-button
          type="danger"
          link
          @click="handleDelete(row)"
          v-if="hasPermission('fuel_rate:delete')"
        >
          删除
        </el-button>
      </template>
    </data-table>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed } from 'vue';
  import { useUserStore } from '@/stores/user';
  import { formatDateTime, formatPercent } from '@/utils/format';
  import type { FuelRate } from '@/api/fuel';
  import { DataTable } from '@/components/common';
  import { usePermission } from '@/composables/usePermission';

  const props = defineProps<{
    data: FuelRate[];
    loading: boolean;
    total: number;
  }>();

  const emit = defineEmits<{
    (e: 'update:current-page', page: number): void;
    (e: 'update:page-size', size: number): void;
    (e: 'edit', row: FuelRate): void;
    (e: 'delete', row: FuelRate): void;
  }>();

  const userStore = useUserStore();
  const { hasPermission } = userStore;

  const currentPage = ref(1);
  const pageSize = ref(10);

  const handlePaginationChange = (pagination: { currentPage: number; pageSize: number }) => {
    if (pagination.pageSize !== pageSize.value) {
      emit('update:page-size', pagination.pageSize);
    }
    if (pagination.currentPage !== currentPage.value) {
      emit('update:current-page', pagination.currentPage);
    }
  };

  const handleEdit = (row: FuelRate) => {
    emit('edit', row);
  };

  const handleDelete = (row: FuelRate) => {
    emit('delete', row);
  };

  const columns = [
    { prop: 'provider', label: '服务商', minWidth: 120 },
    { prop: 'rate', label: '费率', minWidth: 120 },
    { prop: 'effective_date', label: '生效日期', minWidth: 180 },
    { prop: 'expiry_date', label: '失效日期', minWidth: 180 },
    { prop: 'is_active', label: '状态', width: 100 },
    { prop: 'created_at', label: '创建时间', minWidth: 180 },
    { prop: 'actions', label: '操作', width: 200, fixed: 'right' as const },
  ];
</script>

<style scoped>
  .fuel-rate-table {
    width: 100%;
    background-color: var(--bg-color);
    border-radius: var(--border-radius-base);
    box-shadow: var(--box-shadow-light);
  }
</style>
