<template>
  <div class="theme-settings">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>主题设置</span>
        </div>
      </template>

      <el-form :model="form" label-width="120px">
        <el-form-item label="主题模式">
          <el-radio-group v-model="form.mode">
            <el-radio-button value="light">浅色</el-radio-button>
            <el-radio-button value="dark">深色</el-radio-button>
            <el-radio-button value="auto">跟随系统</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="主题色">
          <el-color-picker v-model="form.primaryColor" show-alpha @change="handleColorChange" />
        </el-form-item>

        <el-form-item label="预设主题">
          <div class="theme-presets">
            <div
              v-for="theme in presetThemes"
              :key="theme.name"
              class="theme-preset-item"
              :style="{ backgroundColor: theme.color }"
              @click="handlePresetSelect(theme)"
            >
              <el-icon v-if="form.primaryColor === theme.color">
                <Check />
              </el-icon>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="紧凑模式">
          <el-switch v-model="form.compact" />
        </el-form-item>

        <el-form-item label="圆角大小">
          <el-slider v-model="form.borderRadius" :min="0" :max="20" :step="2" show-input />
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
  import { Check } from '@element-plus/icons-vue';

  const form = ref({
    mode: 'light',
    primaryColor: '#409EFF',
    compact: false,
    borderRadius: 4,
  });

  const presetThemes = [
    { name: '默认蓝', color: '#409EFF' },
    { name: '科技绿', color: '#67C23A' },
    { name: '活力橙', color: '#E6A23C' },
    { name: '优雅紫', color: '#722ED1' },
    { name: '沉稳蓝', color: '#1890FF' },
    { name: '清新青', color: '#13C2C2' },
  ];

  const handleColorChange = (color: string | null) => {
    if (color) {
      form.value.primaryColor = color;
    }
    // 这里可以添加实时预览效果的逻辑
  };

  const handlePresetSelect = (theme: { name: string; color: string }) => {
    form.value.primaryColor = theme.color;
    ElMessage.success(`已选择${theme.name}主题`);
  };

  const handleSave = () => {
    // 这里添加保存主题设置的逻辑
    ElMessage.success('主题设置已保存');
  };

  const handleReset = () => {
    form.value = {
      mode: 'light',
      primaryColor: '#409EFF',
      compact: false,
      borderRadius: 4,
    };
    ElMessage.info('设置已重置');
  };
</script>

<style scoped>
  .theme-settings {
    padding: 20px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .theme-presets {
    display: flex;
    gap: 12px;
    margin-top: 8px;
  }

  .theme-preset-item {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s;
    border: 2px solid transparent;
  }

  .theme-preset-item:hover {
    transform: scale(1.05);
  }

  .theme-preset-item .el-icon {
    color: white;
    font-size: 20px;
  }

  .el-slider {
    width: 100%;
    max-width: 300px;
  }
</style>
