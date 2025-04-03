<template>
  <div class="data-export">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>数据导出</h2>
        </div>
      </template>

      <div class="export-container">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="计算记录" name="calculator">
            <div class="export-form">
              <el-form :model="exportForm" label-width="100px">
                <el-form-item label="时间范围">
                  <el-date-picker
                    v-model="exportForm.dateRange"
                    type="daterange"
                    range-separator="至"
                    start-placeholder="开始日期"
                    end-placeholder="结束日期"
                    style="width: 350px"
                    value-format="YYYY-MM-DD"
                  />
                </el-form-item>
                <el-form-item label="计算类型">
                  <el-select v-model="exportForm.calcType" placeholder="请选择计算类型" style="width: 350px">
                    <el-option label="全部" value="" />
                    <el-option label="单次计算" value="single" />
                    <el-option label="批量计算" value="batch" />
                  </el-select>
                </el-form-item>
                <el-form-item label="文件格式">
                  <el-radio-group v-model="exportForm.fileFormat">
                    <el-radio value="xlsx">Excel (.xlsx)</el-radio>
                    <el-radio value="csv">CSV (.csv)</el-radio>
                    <el-radio value="pdf">PDF (.pdf)</el-radio>
                  </el-radio-group>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="handleExport('calculator')">导出数据</el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="费用报表" name="cost">
            <div class="export-form">
              <el-form :model="exportForm" label-width="100px">
                <el-form-item label="报表周期">
                  <el-select v-model="exportForm.period" placeholder="请选择报表周期" style="width: 350px">
                    <el-option label="日报" value="daily" />
                    <el-option label="周报" value="weekly" />
                    <el-option label="月报" value="monthly" />
                    <el-option label="季报" value="quarterly" />
                    <el-option label="年报" value="yearly" />
                  </el-select>
                </el-form-item>
                <el-form-item label="时间范围">
                  <el-date-picker
                    v-model="exportForm.dateRange"
                    type="daterange"
                    range-separator="至"
                    start-placeholder="开始日期"
                    end-placeholder="结束日期"
                    style="width: 350px"
                    value-format="YYYY-MM-DD"
                  />
                </el-form-item>
                <el-form-item label="服务商">
                  <el-select 
                    v-model="exportForm.providers" 
                    multiple 
                    placeholder="请选择服务商" 
                    style="width: 350px"
                  >
                    <el-option label="FedEx" value="fedex" />
                    <el-option label="UPS" value="ups" />
                    <el-option label="DHL" value="dhl" />
                  </el-select>
                </el-form-item>
                <el-form-item label="文件格式">
                  <el-radio-group v-model="exportForm.fileFormat">
                    <el-radio value="xlsx">Excel (.xlsx)</el-radio>
                    <el-radio value="csv">CSV (.csv)</el-radio>
                    <el-radio value="pdf">PDF (.pdf)</el-radio>
                  </el-radio-group>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="handleExport('cost')">导出数据</el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="系统日志" name="logs">
            <div class="export-form">
              <el-form :model="exportForm" label-width="100px">
                <el-form-item label="日志类型">
                  <el-select v-model="exportForm.logType" placeholder="请选择日志类型" style="width: 350px">
                    <el-option label="全部日志" value="" />
                    <el-option label="操作日志" value="operation" />
                    <el-option label="系统日志" value="system" />
                    <el-option label="错误日志" value="error" />
                  </el-select>
                </el-form-item>
                <el-form-item label="时间范围">
                  <el-date-picker
                    v-model="exportForm.dateRange"
                    type="datetimerange"
                    range-separator="至"
                    start-placeholder="开始时间"
                    end-placeholder="结束时间"
                    style="width: 350px"
                    value-format="YYYY-MM-DD HH:mm:ss"
                  />
                </el-form-item>
                <el-form-item label="用户">
                  <el-select v-model="exportForm.user" placeholder="请选择用户" style="width: 350px">
                    <el-option label="全部用户" value="" />
                    <el-option label="管理员" value="admin" />
                    <el-option label="操作员" value="operator" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="handleExport('logs')">导出数据</el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-tab-pane>
        </el-tabs>
        
        <div class="export-history">
          <h3>导出历史</h3>
          <el-table :data="exportHistory" border style="width: 100%">
            <el-table-column prop="date" label="导出时间" width="180" />
            <el-table-column prop="type" label="导出类型" width="120" />
            <el-table-column prop="fileName" label="文件名称" />
            <el-table-column prop="size" label="文件大小" width="100" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'completed' ? 'success' : (row.status === 'failed' ? 'danger' : 'warning')">
                  {{ row.status === 'completed' ? '完成' : (row.status === 'failed' ? '失败' : '进行中') }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button v-if="row.status === 'completed'" type="primary" link>下载</el-button>
                <el-button v-if="row.status === 'completed'" type="danger" link>删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { ElMessage } from 'element-plus';

// 当前活动标签
const activeTab = ref('calculator');

// 导出表单类型定义
interface ExportFormState {
  dateRange: any;
  calcType: string;
  fileFormat: string;
  period: string;
  providers: string[];
  logType: string;
  user: string;
}

// 导出表单
const exportForm = reactive<ExportFormState>({
  dateRange: '',
  calcType: '',
  fileFormat: 'xlsx',
  period: 'monthly',
  providers: [],
  logType: '',
  user: ''
});

// 导出历史
const exportHistory = ref([
  {
    date: '2024-03-10 10:15:23',
    type: '计算记录',
    fileName: '计算记录_20240301-20240310.xlsx',
    size: '1.2MB',
    status: 'completed'
  },
  {
    date: '2024-03-08 15:32:10',
    type: '费用报表',
    fileName: '费用月报_202402.pdf',
    size: '3.5MB',
    status: 'completed'
  },
  {
    date: '2024-03-07 09:05:47',
    type: '系统日志',
    fileName: '系统日志_20240301-20240307.csv',
    size: '0.8MB',
    status: 'completed'
  },
  {
    date: '2024-03-05 14:22:36',
    type: '费用报表',
    fileName: '费用季报_2023Q4.xlsx',
    size: '5.3MB',
    status: 'completed'
  },
  {
    date: '2024-03-01 11:45:19',
    type: '计算记录',
    fileName: '计算记录_20240201-20240229.xlsx',
    size: '2.1MB',
    status: 'completed'
  }
]);

// 导出方法
const handleExport = (type: string) => {
  if (!exportForm.dateRange) {
    ElMessage.warning('请选择时间范围');
    return;
  }

  // 根据不同类型执行导出
  if (type === 'calculator') {
    ElMessage.success('计算记录导出任务已提交，请稍后查看导出历史');
  } else if (type === 'cost') {
    ElMessage.success('费用报表导出任务已提交，请稍后查看导出历史');
  } else if (type === 'logs') {
    ElMessage.success('系统日志导出任务已提交，请稍后查看导出历史');
  }
  
  // 模拟新增导出历史记录
  exportHistory.value.unshift({
    date: new Date().toLocaleString(),
    type: type === 'calculator' ? '计算记录' : (type === 'cost' ? '费用报表' : '系统日志'),
    fileName: `导出任务_${new Date().getTime()}.${exportForm.fileFormat}`,
    size: '处理中',
    status: 'processing'
  });
};
</script>

<style scoped>
.data-export {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.export-container {
  margin-top: 20px;
}

.export-form {
  max-width: 800px;
  margin: 20px auto;
  padding: 20px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 4px;
}

.export-history {
  margin-top: 40px;
}

.export-history h3 {
  margin-bottom: 15px;
}
</style> 