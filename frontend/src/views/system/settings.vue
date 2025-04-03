<template>
  <div class="settings-container">
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <h3>系统设置</h3>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        label-width="120px"
        class="settings-form"
      >
        <el-form-item label="系统名称">
          <el-input v-model="form.systemName" />
        </el-form-item>

        <el-form-item label="默认语言">
          <el-select v-model="form.language" style="width: 100%">
            <el-option label="简体中文" value="zh-CN" />
            <el-option label="English" value="en-US" />
          </el-select>
        </el-form-item>

        <el-form-item label="主题">
          <el-select v-model="form.theme" style="width: 100%">
            <el-option label="浅色" value="light" />
            <el-option label="深色" value="dark" />
          </el-select>
        </el-form-item>

        <el-form-item label="时区">
          <el-select v-model="form.timezone" style="width: 100%">
            <el-option label="(GMT+8:00) 北京" value="Asia/Shanghai" />
            <el-option label="(GMT+0:00) 伦敦" value="Europe/London" />
            <el-option label="(GMT-5:00) 纽约" value="America/New_York" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit">保存设置</el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import type { FormInstance } from 'element-plus';

const formRef = ref<FormInstance>();
const form = ref({
  systemName: '物流运费计算系统',
  language: 'zh-CN',
  theme: 'light',
  timezone: 'Asia/Shanghai'
});

const handleSubmit = async () => {
  try {
    ElMessage.success('设置保存成功');
  } catch (error) {
    ElMessage.error('保存失败');
  }
};

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields();
  }
};
</script>

<style scoped>
.settings-container {
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

.settings-form {
  margin-top: 20px;
}
</style>
