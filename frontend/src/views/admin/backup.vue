<template>
  <div class="backup-container">
    <el-row :gutter="20">
      <!-- 备份操作 -->
      <el-col :span="24">
        <el-card class="mb-4">
          <template #header>
            <div class="card-header">
              <span>数据备份</span>
              <el-button-group>
                <el-button type="primary" @click="createBackup">
                  <el-icon><Plus /></el-icon>
                  创建备份
                </el-button>
                <el-button type="success" @click="scheduleBackup">
                  <el-icon><Timer /></el-icon>
                  定时备份
                </el-button>
              </el-button-group>
            </div>
          </template>

          <el-form :model="backupConfig" label-width="120px">
            <el-form-item label="备份类型">
              <el-radio-group v-model="backupConfig.type">
                <el-radio-button value="full">完整备份</el-radio-button>
                <el-radio-button value="incremental">增量备份</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="备份内容">
              <el-checkbox-group v-model="backupConfig.content">
                <el-checkbox label="database">数据库</el-checkbox>
                <el-checkbox label="files">文件</el-checkbox>
                <el-checkbox label="config">配置</el-checkbox>
                <el-checkbox label="logs">日志</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item label="压缩方式">
              <el-select v-model="backupConfig.compression">
                <el-option label="不压缩" value="none" />
                <el-option label="ZIP压缩" value="zip" />
                <el-option label="高压缩" value="7z" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 备份历史 -->
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>备份历史</span>
              <el-button type="danger" @click="clearHistory">
                清空历史
              </el-button>
            </div>
          </template>

          <el-table :data="backupHistory" style="width: 100%">
            <el-table-column type="expand">
              <template #default="props">
                <div class="backup-detail">
                  <el-descriptions :column="2" border>
                    <el-descriptions-item label="备份内容">
                      {{ props.row.content.join(', ') }}
                    </el-descriptions-item>
                    <el-descriptions-item label="压缩方式">
                      {{ getCompressionLabel(props.row.compression) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="文件大小">
                      {{ formatFileSize(props.row.size) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="MD5校验">
                      {{ props.row.md5 }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="id" label="备份ID" width="120" />
            <el-table-column prop="type" label="类型" width="120">
              <template #default="scope">
                <el-tag :type="scope.row.type === 'full' ? 'success' : 'warning'">
                  {{ scope.row.type === 'full' ? '完整备份' : '增量备份' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="120">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">
                  {{ getStatusLabel(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column prop="completed_at" label="完成时间" width="180" />
            <el-table-column label="操作" width="250" fixed="right">
              <template #default="scope">
                <el-button-group>
                  <el-button 
                    type="primary" 
                    :disabled="scope.row.status !== 'completed'"
                    @click="downloadBackup(scope.row)"
                  >
                    下载
                  </el-button>
                  <el-button 
                    type="success" 
                    :disabled="scope.row.status !== 'completed'"
                    @click="restoreBackup(scope.row)"
                  >
                    恢复
                  </el-button>
                  <el-button 
                    type="danger" 
                    @click="deleteBackup(scope.row)"
                  >
                    删除
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 定时备份对话框 -->
    <el-dialog v-model="scheduleDialogVisible" title="定时备份设置" width="500px">
      <el-form :model="scheduleForm" label-width="100px">
        <el-form-item label="执行周期">
          <el-select v-model="scheduleForm.cycle">
            <el-option label="每天" value="daily" />
            <el-option label="每周" value="weekly" />
            <el-option label="每月" value="monthly" />
          </el-select>
        </el-form-item>

        <el-form-item label="执行时间">
          <el-time-picker
            v-model="scheduleForm.time"
            format="HH:mm"
            placeholder="选择时间"
          />
        </el-form-item>

        <el-form-item label="保留份数">
          <el-input-number
            v-model="scheduleForm.keepCount"
            :min="1"
            :max="30"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="scheduleDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveSchedule">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Timer } from '@element-plus/icons-vue';

// 备份配置
const backupConfig = ref({
  type: 'full',
  content: ['database'],
  compression: 'zip'
});

// 定时备份配置
const scheduleDialogVisible = ref(false);
const scheduleForm = ref({
  cycle: 'daily',
  time: new Date(2024, 2, 8, 2, 0),
  keepCount: 7
});

// 备份历史
const backupHistory = ref([
  {
    id: 'BK20240308001',
    type: 'full',
    status: 'completed',
    content: ['database', 'files', 'config'],
    compression: 'zip',
    size: 1024 * 1024 * 256, // 256MB
    md5: 'e10adc3949ba59abbe56e057f20f883e',
    created_at: '2024-03-08 02:00:00',
    completed_at: '2024-03-08 02:05:32'
  },
  {
    id: 'BK20240308002',
    type: 'incremental',
    status: 'completed',
    content: ['database'],
    compression: 'zip',
    size: 1024 * 1024 * 50, // 50MB
    md5: '098f6bcd4621d373cade4e832627b4f6',
    created_at: '2024-03-08 14:00:00',
    completed_at: '2024-03-08 14:01:15'
  },
  {
    id: 'BK20240308003',
    type: 'full',
    status: 'failed',
    content: ['database', 'files', 'config', 'logs'],
    compression: '7z',
    size: 0,
    md5: '',
    created_at: '2024-03-08 15:30:00',
    completed_at: null
  }
]);

// 创建备份
const createBackup = () => {
  if (backupConfig.value.content.length === 0) {
    ElMessage.warning('请至少选择一项备份内容');
    return;
  }

  ElMessageBox.confirm(
    '确定要创建新的备份吗？备份过程中可能会影响系统性能。',
    '创建备份',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    ElMessage.success('备份任务已创建，请在备份历史中查看进度');
  });
};

// 定时备份
const scheduleBackup = () => {
  scheduleDialogVisible.value = true;
};

// 保存定时备份设置
const saveSchedule = () => {
  scheduleDialogVisible.value = false;
  ElMessage.success('定时备份设置已保存');
};

// 下载备份
const downloadBackup = (backup: any) => {
  ElMessage.success(`开始下载备份文件：${backup.id}`);
};

// 恢复备份
const restoreBackup = (backup: any) => {
  ElMessageBox.confirm(
    '恢复备份将覆盖当前数据，是否继续？',
    '恢复确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    ElMessage.success('备份恢复任务已创建');
  });
};

// 删除备份
const deleteBackup = (backup: any) => {
  ElMessageBox.confirm(
    '确定要删除该备份吗？删除后将无法恢复。',
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    backupHistory.value = backupHistory.value.filter(b => b.id !== backup.id);
    ElMessage.success('备份已删除');
  });
};

// 清空历史
const clearHistory = () => {
  ElMessageBox.confirm(
    '确定要清空所有备份历史记录吗？',
    '清空确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    backupHistory.value = [];
    ElMessage.success('备份历史已清空');
  });
};

// 获取压缩方式标签
const getCompressionLabel = (compression: string) => {
  const labels: Record<string, string> = {
    none: '不压缩',
    zip: 'ZIP压缩',
    '7z': '高压缩'
  };
  return labels[compression] || compression;
};

// 获取状态类型
const getStatusType = (status: string): 'success' | 'warning' | 'danger' => {
  switch (status) {
    case 'completed':
      return 'success';
    case 'in_progress':
      return 'warning';
    case 'failed':
      return 'danger';
    default:
      return 'warning';
  }
};

// 获取状态标签
const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    completed: '已完成',
    in_progress: '进行中',
    failed: '失败'
  };
  return labels[status] || status;
};

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};
</script>

<style scoped>
.backup-container {
  padding: 20px;
}

.mb-4 {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.backup-detail {
  padding: 20px;
}

:deep(.el-descriptions) {
  margin-bottom: 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style> 