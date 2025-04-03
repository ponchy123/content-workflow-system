<template>
  <div class="admin-settings">
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <h3>系统设置</h3>
        </div>
      </template>

      <el-form :model="settings" label-width="120px">
        <el-form-item label="系统名称">
          <el-input v-model="settings.systemName" />
        </el-form-item>

        <el-form-item label="系统描述">
          <el-input v-model="settings.systemDescription" type="textarea" />
        </el-form-item>

        <el-form-item label="维护模式">
          <el-switch v-model="settings.maintenanceMode" />
        </el-form-item>

        <el-form-item label="缓存设置">
          <el-select v-model="settings.cacheStrategy" style="width: 100%">
            <el-option label="Redis" value="redis" />
            <el-option label="内存缓存" value="memory" />
            <el-option label="文件缓存" value="file" />
          </el-select>
        </el-form-item>

        <el-form-item label="日志级别">
          <el-select v-model="settings.logLevel" style="width: 100%">
            <el-option label="DEBUG" value="debug" />
            <el-option label="INFO" value="info" />
            <el-option label="WARNING" value="warning" />
            <el-option label="ERROR" value="error" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="saveSettings">保存设置</el-button>
          <el-button @click="resetSettings">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';

const settings = ref({
  systemName: '运费计算系统',
  systemDescription: '智能运费计算及管理系统',
  maintenanceMode: false,
  cacheStrategy: 'redis',
  logLevel: 'info'
});

const saveSettings = async () => {
  try {
    // TODO: 实现保存设置的API调用
    ElMessage.success('设置保存成功');
  } catch (error) {
    ElMessage.error('保存设置失败');
  }
};

const resetSettings = () => {
  settings.value = {
    systemName: '运费计算系统',
    systemDescription: '智能运费计算及管理系统',
    maintenanceMode: false,
    cacheStrategy: 'redis',
    logLevel: 'info'
  };
};
</script>

<style scoped>
.admin-settings {
  padding: 20px;
}

.settings-card {
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 