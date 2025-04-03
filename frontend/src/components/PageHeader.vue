<template>
  <div class="page-header">
    <div class="header-content">
      <div class="title-container">
        <h1 class="title">{{ title }}</h1>
        <p v-if="subtitle" class="subtitle">{{ subtitle }}</p>
      </div>
      <div class="actions-container">
        <slot name="actions"></slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  }
});
</script>

<style scoped>
.page-header {
  margin-bottom: 20px;
  background-color: #fff;
  border-radius: 4px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
}

.title-container {
  flex: 1;
}

.title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0;
  padding: 0;
  line-height: 1.5;
}

.subtitle {
  font-size: 14px;
  color: #909399;
  margin: 8px 0 0 0;
  padding: 0;
  line-height: 1.5;
}

.actions-container {
  display: flex;
  gap: 10px;
}
</style> 