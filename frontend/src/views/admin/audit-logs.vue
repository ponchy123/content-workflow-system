<template>
  <div class="page-container">
    <el-card class="mb-base">
      <div class="page-header">
        <h1 class="page-title">审计日志</h1>
        <div class="flex gap-base">
          <el-button @click="refreshLogs">
            <el-icon><Refresh /></el-icon>刷新
          </el-button>
          <el-button type="danger" @click="handleClearLogs">
            <el-icon><Delete /></el-icon>清空日志
          </el-button>
        </div>
      </div>
    </el-card>

    <el-card class="mb-base">
      <el-form :inline="true" :model="filterForm" class="flex flex-wrap gap-base">
        <el-form-item label="操作类型">
          <el-select v-model="filterForm.operationType" placeholder="请选择操作类型" clearable>
            <el-option
              v-for="type in operationTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="操作人">
          <el-input v-model="filterForm.operator" placeholder="请输入操作人" clearable />
        </el-form-item>
        <el-form-item label="操作时间">
          <el-date-picker
            v-model="filterForm.timeRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>搜索
          </el-button>
          <el-button @click="resetFilter">
            <el-icon><Refresh /></el-icon>重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table v-loading="loading" :data="logList" border stripe style="width: 100%">
        <el-table-column type="index" width="50" align="center" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="ip" label="IP地址" min-width="120" />
        <el-table-column prop="action" label="操作内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="module" label="操作模块" min-width="120" />
        <el-table-column prop="action_type" label="操作类型" min-width="120">
          <template #default="scope">
            <el-tag :type="getActionTypeTag(scope.row.action_type) as any" size="small">
              {{ getActionTypeLabel(scope.row.action_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="scope">
            <el-tag :type="scope.row.status ? 'success' : 'danger'" size="small">
              {{ scope.row.status ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="操作时间" min-width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="scope">
            <el-tooltip effect="dark" content="查看详情" placement="top">
              <el-button type="primary" link @click="handleViewLog(scope.row)">
                <el-icon><View /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip effect="dark" content="删除日志" placement="top">
              <el-button
                type="danger"
                link
                @click="handleDeleteLog(scope.row)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <div class="flex justify-center mt-base">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 日志详情对话框 -->
    <el-dialog v-model="dialogVisible" title="日志详情" width="800px" destroy-on-close>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用户名">{{ currentLog.username }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ currentLog.ip }}</el-descriptions-item>
        <el-descriptions-item label="浏览器">{{ currentLog.browser }}</el-descriptions-item>
        <el-descriptions-item label="操作系统">{{ currentLog.os }}</el-descriptions-item>
        <el-descriptions-item label="操作模块">{{ currentLog.module }}</el-descriptions-item>
        <el-descriptions-item label="操作类型">
          <el-tag :type="getActionTypeTag(currentLog.action_type) as any" size="small">
            {{ getActionTypeLabel(currentLog.action_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="操作状态">
          <el-tag :type="currentLog.status ? 'success' : 'danger'" size="small">
            {{ currentLog.status ? '成功' : '失败' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="操作时间">{{
          formatDateTime(currentLog.created_at)
        }}</el-descriptions-item>
        <el-descriptions-item label="操作内容" :span="2">{{
          currentLog.action
        }}</el-descriptions-item>
        <el-descriptions-item label="请求参数" :span="2">
          <el-input type="textarea" v-model="currentLog.request_param" :rows="5" readonly />
        </el-descriptions-item>
        <el-descriptions-item v-if="currentLog.error_msg" label="错误信息" :span="2">
          <el-input type="textarea" v-model="currentLog.error_msg" :rows="3" readonly />
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 活动趋势图 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <h3>操作趋势分析</h3>
          <div class="chart-actions">
            <el-radio-group v-model="chartTimeUnit" size="small" @change="updateChartData">
              <el-radio-button value="hour">小时</el-radio-button>
              <el-radio-button value="day">天</el-radio-button>
              <el-radio-button value="week">周</el-radio-button>
              <el-radio-button value="month">月</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>
      <div class="chart-container" ref="chartContainer"></div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, onMounted, nextTick, onBeforeUnmount } from 'vue';
  import { ElMessage, ElMessageBox } from 'element-plus';
  import { formatDateTime } from '@/utils/format';
  import { View, Delete, Search, Refresh, Download } from '@element-plus/icons-vue';
  import * as echarts from 'echarts';

  // 操作类型选项
  const operationTypes = [
    { value: 'login', label: '登录' },
    { value: 'logout', label: '登出' },
    { value: 'create', label: '新增' },
    { value: 'update', label: '更新' },
    { value: 'delete', label: '删除' },
    { value: 'query', label: '查询' },
    { value: 'import', label: '导入' },
    { value: 'export', label: '导出' },
    { value: 'other', label: '其他' },
  ];

  // 日期快捷选项
  const dateShortcuts = [
    {
      text: '最近一天',
      value: () => {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24);
        return [start, end];
      },
    },
    {
      text: '最近一周',
      value: () => {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
        return [start, end];
      },
    },
    {
      text: '最近一个月',
      value: () => {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
        return [start, end];
      },
    },
    {
      text: '最近三个月',
      value: () => {
        const end = new Date();
        const start = new Date();
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
        return [start, end];
      },
    },
  ];

  // 日志数据接口
  interface AuditLog {
    id: string;
    username: string;
    ip: string;
    module: string;
    action: string;
    action_type: string;
    request_param: string;
    status: boolean;
    error_msg?: string;
    browser: string;
    os: string;
    created_at: string;
  }

  // 列表数据
  const loading = ref(false);
  const logList = ref<AuditLog[]>([]);
  const currentPage = ref(1);
  const pageSize = ref(10);
  const total = ref(0);

  // 筛选表单
  const filterForm = reactive({
    operationType: '',
    operator: '',
    timeRange: [] as string[],
  });

  // 日志详情对话框
  const dialogVisible = ref(false);
  const currentLog = ref<AuditLog>({} as AuditLog);

  // 图表数据
  const chartContainer = ref<HTMLElement>();
  const chartTimeUnit = ref('day');
  let chart: echarts.ECharts | null = null;

  // 获取日志列表
  const fetchLogsList = async () => {
    loading.value = true;
    try {
      // 模拟后端API请求
      await new Promise(resolve => setTimeout(resolve, 500));

      // 模拟日志数据
      const mockLogs = Array.from({ length: 50 }, (_, i) => {
        const isSuccess = Math.random() > 0.2;
        const actionType = operationTypes[Math.floor(Math.random() * operationTypes.length)].value;
        const username = `user${Math.floor(Math.random() * 10) + 1}`;
        const date = new Date();
        date.setTime(date.getTime() - Math.random() * 90 * 24 * 3600 * 1000);

        return {
          id: `log-${i + 1}`,
          username,
          ip: `192.168.1.${Math.floor(Math.random() * 255) + 1}`,
          module: ['用户管理', '角色管理', '权限管理', '产品管理', '燃油费率管理'][
            Math.floor(Math.random() * 5)
          ],
          action: getRandomAction(actionType, username),
          action_type: actionType,
          request_param: JSON.stringify(
            {
              id: `user-${Math.floor(Math.random() * 10) + 1}`,
              method: 'POST',
              params: { pageNum: 1, pageSize: 10 },
            },
            null,
            2,
          ),
          status: isSuccess,
          error_msg: isSuccess ? undefined : '权限不足，无法执行该操作',
          browser: ['Chrome', 'Firefox', 'Safari', 'Edge'][Math.floor(Math.random() * 4)],
          os: ['Windows', 'MacOS', 'Linux', 'iOS', 'Android'][Math.floor(Math.random() * 5)],
          created_at: date.toISOString(),
        };
      });

      // 按时间倒序排序
      mockLogs.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

      // 筛选
      let filteredLogs = [...mockLogs];
      if (filterForm.operator) {
        filteredLogs = filteredLogs.filter(log =>
          log.username.toLowerCase().includes(filterForm.operator.toLowerCase()),
        );
      }

      if (filterForm.operationType) {
        filteredLogs = filteredLogs.filter(log => log.action_type === filterForm.operationType);
      }

      if (filterForm.timeRange && filterForm.timeRange.length === 2) {
        const startTime = new Date(filterForm.timeRange[0]).getTime();
        const endTime = new Date(filterForm.timeRange[1]).getTime();

        filteredLogs = filteredLogs.filter(log => {
          const logTime = new Date(log.created_at).getTime();
          return logTime >= startTime && logTime <= endTime;
        });
      }

      total.value = filteredLogs.length;

      // 分页
      const start = (currentPage.value - 1) * pageSize.value;
      const end = start + pageSize.value;
      logList.value = filteredLogs.slice(start, end);

      // 更新图表数据
      updateChartData();
    } catch (error) {
      console.error('获取日志列表失败:', error);
      ElMessage.error('获取日志列表失败');
    } finally {
      loading.value = false;
    }
  };

  // 获取随机操作内容
  const getRandomAction = (actionType: string, username: string): string => {
    switch (actionType) {
      case 'login':
        return `用户 ${username} 登录系统`;
      case 'logout':
        return `用户 ${username} 退出系统`;
      case 'create':
        return `用户 ${username} 新增了一条数据`;
      case 'update':
        return `用户 ${username} 更新了一条数据`;
      case 'delete':
        return `用户 ${username} 删除了一条数据`;
      case 'query':
        return `用户 ${username} 查询了数据列表`;
      case 'import':
        return `用户 ${username} 导入了数据`;
      case 'export':
        return `用户 ${username} 导出了数据`;
      default:
        return `用户 ${username} 执行了操作`;
    }
  };

  // 搜索
  const handleSearch = () => {
    currentPage.value = 1;
    fetchLogsList();
  };

  // 重置筛选条件
  const resetFilter = () => {
    filterForm.operationType = '';
    filterForm.operator = '';
    filterForm.timeRange = [];
    handleSearch();
  };

  // 刷新日志列表
  const refreshLogs = () => {
    fetchLogsList();
  };

  // 分页处理
  const handleSizeChange = (val: number) => {
    pageSize.value = val;
    fetchLogsList();
  };

  const handleCurrentChange = (val: number) => {
    currentPage.value = val;
    fetchLogsList();
  };

  // 查看日志详情
  const handleViewLog = (row: AuditLog) => {
    currentLog.value = row;
    dialogVisible.value = true;
  };

  // 删除日志
  const handleDeleteLog = (row: AuditLog) => {
    ElMessageBox.confirm('确定要删除该日志记录吗？', '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
      .then(async () => {
        try {
          loading.value = true;

          // 模拟API调用
          await new Promise(resolve => setTimeout(resolve, 500));

          // 从本地列表中移除
          logList.value = logList.value.filter(log => log.id !== row.id);
          total.value--;

          ElMessage.success('删除日志成功');
        } catch (error) {
          console.error('删除日志失败:', error);
          ElMessage.error('删除日志失败');
        } finally {
          loading.value = false;
        }
      })
      .catch(() => {
        // 取消删除
      });
  };

  // 导出日志
  const exportLogs = () => {
    ElMessage.success('日志导出成功');
  };

  // 清空日志
  const handleClearLogs = async () => {
    try {
      await ElMessageBox.confirm('确定要清空所有日志记录吗？', '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      });
      
      loading.value = true;
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500));
      logList.value = [];
      total.value = 0;
      ElMessage.success('日志清空成功');
    } catch (error) {
      if (error !== 'cancel') {
        ElMessage.error('清空日志失败');
      }
    } finally {
      loading.value = false;
    }
  };

  // 获取操作类型标签类型
  const getActionTypeTag = (
    actionType: string,
  ): 'success' | 'warning' | 'info' | 'danger' | 'primary' | '' => {
    switch (actionType) {
      case 'login':
      case 'logout':
        return 'info';
      case 'create':
        return 'success';
      case 'update':
        return 'warning';
      case 'delete':
        return 'danger';
      case 'query':
        return 'primary';
      case 'import':
      case 'export':
        return '';
      default:
        return '';
    }
  };

  // 获取操作类型标签文本
  const getActionTypeLabel = (actionType: string): string => {
    const type = operationTypes.find(t => t.value === actionType);
    return type ? type.label : actionType;
  };

  // 初始化图表
  const initChart = () => {
    if (!chartContainer.value) return;

    if (chart) {
      chart.dispose();
    }

    chart = echarts.init(chartContainer.value);

    chart.setOption({
      title: {
        text: '操作日志统计',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
      },
      legend: {
        data: ['成功', '失败', '总数'],
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: [],
      },
      yAxis: {
        type: 'value',
      },
      series: [
        {
          name: '成功',
          type: 'bar',
          stack: 'total',
          emphasis: {
            focus: 'series',
          },
          data: [],
        },
        {
          name: '失败',
          type: 'bar',
          stack: 'total',
          emphasis: {
            focus: 'series',
          },
          data: [],
        },
        {
          name: '总数',
          type: 'line',
          emphasis: {
            focus: 'series',
          },
          data: [],
        },
      ],
    });

    window.addEventListener('resize', resizeChart);
  };

  const resizeChart = () => {
    chart?.resize();
  };

  // 更新图表数据
  const updateChartData = () => {
    if (!chart) return;

    const timeLabels: string[] = [];
    const successData: number[] = [];
    const failData: number[] = [];
    const totalData: number[] = [];

    // 根据选择的时间单位生成统计数据
    switch (chartTimeUnit.value) {
      case 'hour':
        // 按小时统计最近24小时
        for (let i = 0; i < 24; i++) {
          const date = new Date();
          date.setHours(date.getHours() - i);
          const hourStr = date.getHours().toString().padStart(2, '0') + ':00';
          timeLabels.unshift(hourStr);

          // 模拟数据
          const total = Math.floor(Math.random() * 100);
          const fail = Math.floor(Math.random() * (total * 0.3));
          const success = total - fail;

          successData.unshift(success);
          failData.unshift(fail);
          totalData.unshift(total);
        }
        break;

      case 'day':
        // 按天统计最近7天
        for (let i = 0; i < 7; i++) {
          const date = new Date();
          date.setDate(date.getDate() - i);
          const dateStr = `${date.getMonth() + 1}/${date.getDate()}`;
          timeLabels.unshift(dateStr);

          // 模拟数据
          const total = Math.floor(Math.random() * 500);
          const fail = Math.floor(Math.random() * (total * 0.2));
          const success = total - fail;

          successData.unshift(success);
          failData.unshift(fail);
          totalData.unshift(total);
        }
        break;

      case 'week':
        // 按周统计最近4周
        for (let i = 0; i < 4; i++) {
          const date = new Date();
          date.setDate(date.getDate() - i * 7);
          const startDate = new Date(date);
          startDate.setDate(date.getDate() - 6);
          const dateStr = `${startDate.getMonth() + 1}/${startDate.getDate()}-${date.getMonth() + 1}/${date.getDate()}`;
          timeLabels.unshift(dateStr);

          // 模拟数据
          const total = Math.floor(Math.random() * 2000);
          const fail = Math.floor(Math.random() * (total * 0.15));
          const success = total - fail;

          successData.unshift(success);
          failData.unshift(fail);
          totalData.unshift(total);
        }
        break;

      case 'month':
        // 按月统计最近6个月
        for (let i = 0; i < 6; i++) {
          const date = new Date();
          date.setMonth(date.getMonth() - i);
          const dateStr = `${date.getFullYear()}/${date.getMonth() + 1}`;
          timeLabels.unshift(dateStr);

          // 模拟数据
          const total = Math.floor(Math.random() * 5000);
          const fail = Math.floor(Math.random() * (total * 0.1));
          const success = total - fail;

          successData.unshift(success);
          failData.unshift(fail);
          totalData.unshift(total);
        }
        break;
    }

    chart.setOption({
      xAxis: {
        data: timeLabels,
      },
      series: [
        {
          name: '成功',
          data: successData,
        },
        {
          name: '失败',
          data: failData,
        },
        {
          name: '总数',
          data: totalData,
        },
      ],
    });
  };

  onMounted(() => {
    fetchLogsList();
    nextTick(() => {
      initChart();
    });
  });

  onBeforeUnmount(() => {
    window.removeEventListener('resize', resizeChart);
    chart?.dispose();
  });
</script>

<style scoped>
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

  .filter-card {
    margin-bottom: 20px;
  }

  .table-card {
    margin-bottom: 20px;
  }

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .chart-card {
    margin-bottom: 20px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .chart-container {
    height: 400px;
    margin-top: 20px;
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

    .chart-container {
      height: 300px;
    }
  }

  .log-content {
    max-height: 400px;
    overflow-y: auto;
    padding: var(--el-spacing-base);
    background-color: var(--el-fill-color-light);
    border-radius: var(--el-border-radius-base);
    font-family: var(--el-font-family-monospace);
    white-space: pre-wrap;
    word-break: break-all;
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: var(--el-spacing-base);
  }

  .operation-tag {
    margin-right: var(--el-spacing-small);
    &:last-child {
      margin-right: 0;
    }
  }
</style>
