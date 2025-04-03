<template>
  <div class="language-settings">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>语言设置</span>
        </div>
      </template>

      <el-form :model="form" label-width="120px">
        <el-form-item label="系统语言">
          <el-select v-model="form.language" class="language-select">
            <el-option
              v-for="lang in languages"
              :key="lang.value"
              :label="lang.label"
              :value="lang.value"
            ></el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="日期格式">
          <el-select v-model="form.dateFormat" class="format-select">
            <el-option
              v-for="format in dateFormats"
              :key="format.value"
              :label="format.label"
              :value="format.value"
            ></el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="时区">
          <el-select v-model="form.timezone" class="timezone-select">
            <el-option
              v-for="zone in timezones"
              :key="zone.value"
              :label="zone.label"
              :value="zone.value"
            ></el-option>
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSave">保存设置</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
  import { ref } from 'vue';
  import { ElMessage } from 'element-plus';

  const form = ref({
    language: 'zh-CN',
    dateFormat: 'YYYY-MM-DD',
    timezone: 'Asia/Shanghai',
  });

  const languages = [
    { value: 'zh-CN', label: '简体中文' },
    { value: 'en-US', label: 'English' },
    { value: 'ja-JP', label: '日本語' },
  ];

  const dateFormats = [
    { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD' },
    { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY' },
    { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY' },
  ];

  const timezones = [
    { value: 'Asia/Shanghai', label: '中国标准时间 (UTC+8)' },
    { value: 'Asia/Tokyo', label: '日本标准时间 (UTC+9)' },
    { value: 'America/New_York', label: '美国东部时间 (UTC-5)' },
  ];

  const handleSave = () => {
    // 这里添加保存设置的逻辑
    ElMessage.success('设置已保存');
  };

  const handleReset = () => {
    form.value = {
      language: 'zh-CN',
      dateFormat: 'YYYY-MM-DD',
      timezone: 'Asia/Shanghai',
    };
    ElMessage.info('设置已重置');
  };
</script>

<style scoped>
  .language-settings {
    padding: 20px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .language-select,
  .format-select,
  .timezone-select {
    width: 100%;
    max-width: 300px;
  }
</style>
