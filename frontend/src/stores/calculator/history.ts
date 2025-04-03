import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { CalculationHistory, HistoryDetail } from '@/types/calculator';
import {
  getHistory,
  getHistoryDetail,
  deleteHistory,
  exportHistory as exportHistoryAPI,
} from '@/api/calculator/history';
import { ElMessage } from 'element-plus';
import * as XLSX from 'xlsx';

export const useHistoryStore = defineStore('history', () => {
  const loading = ref(false);
  const histories = ref<CalculationHistory[]>([]);
  const currentDetail = ref<HistoryDetail | null>(null);
  const pagination = ref({
    page: 1,
    pageSize: 10,
    total: 0,
  });

  // 获取历史记录列表
  const fetchHistories = async (page = 1, pageSize = 10) => {
    loading.value = true;
    try {
      const response = await getHistory(page, pageSize);
      histories.value = response.items;
      pagination.value = {
        page,
        pageSize,
        total: response.total,
      };
      return true;
    } catch (error) {
      console.error('Failed to fetch histories:', error);
      return false;
    } finally {
      loading.value = false;
    }
  };

  // 获取历史记录详情
  const fetchHistoryDetail = async (id: string) => {
    loading.value = true;
    try {
      const response = await getHistoryDetail(id);
      currentDetail.value = response;
      return true;
    } catch (error) {
      console.error('Failed to fetch history detail:', error);
      return false;
    } finally {
      loading.value = false;
    }
  };

  // 清除当前详情
  const clearCurrentDetail = () => {
    currentDetail.value = null;
  };

  // 导出历史记录
  const exportHistory = async (startDate: Date, endDate: Date) => {
    loading.value = true;
    try {
      const response = await exportHistoryAPI(startDate, endDate);
      const workbook = XLSX.read(response, { type: 'array' });
      const worksheet = workbook.Sheets[workbook.SheetNames[0]];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);

      // 创建新的工作表
      const ws = XLSX.utils.json_to_sheet(jsonData);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, '计算历史');

      // 导出文件
      const fileName = `运费计算历史_${startDate.toISOString().split('T')[0]}_${endDate.toISOString().split('T')[0]}.xlsx`;
      XLSX.writeFile(wb, fileName);
      ElMessage.success('导出成功');
    } catch (error) {
      console.error('Failed to export history:', error);
      ElMessage.error('导出失败');
    } finally {
      loading.value = false;
    }
  };

  // 导出详情
  const exportDetail = async (id: string) => {
    if (!currentDetail.value) return;

    try {
      const detail = currentDetail.value;
      const data = [
        {
          请求ID: detail.requestId,
          起始地: detail.request.fromAddress,
          目的地: detail.request.toAddress,
          重量: detail.request.weight,
          产品类型: detail.request.productType,
          基础运费: detail.baseCharge,
          燃油附加费: detail.fuelSurcharge,
          总费用: detail.totalCharge,
          币种: detail.currency,
          状态: detail.status || '成功'
        }
      ];

      const ws = XLSX.utils.json_to_sheet(data);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, '计算详情');

      // 导出文件
      const fileName = `运费计算详情_${id}_${new Date().toISOString().split('T')[0]}.xlsx`;
      XLSX.writeFile(wb, fileName);
      ElMessage.success('导出成功');
    } catch (error) {
      console.error('Export detail failed:', error);
      ElMessage.error('导出失败');
    }
  };

  // 清空历史
  const clearHistory = async () => {
    loading.value = true;
    try {
      await deleteHistory();
      histories.value = [];
      pagination.value.total = 0;
      ElMessage.success('历史记录已清空');
    } catch (error) {
      console.error('Failed to clear history:', error);
      ElMessage.error('清空失败');
    } finally {
      loading.value = false;
    }
  };

  return {
    loading,
    histories,
    currentDetail,
    pagination,
    fetchHistories,
    fetchHistoryDetail,
    clearCurrentDetail,
    exportHistory,
    exportDetail,
    clearHistory,
  };
});
