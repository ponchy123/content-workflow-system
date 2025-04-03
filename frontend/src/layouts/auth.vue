<template>
  <div class="auth-layout">
    <div class="auth-content">
      <div class="auth-header">
        <h1 class="auth-title">物流运费订单计算系统</h1>
        <p class="auth-subtitle">登录以继续使用</p>
      </div>
      <div class="auth-container">
        <router-view />
      </div>
    </div>
    <div class="auth-footer">
      <p>&copy; 2025 物流运费订单计算系统. All rights reserved.</p>
    </div>
  </div>
</template>

<style scoped>
  .auth-layout {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, var(--auth-bg-gradient-start) 0%, var(--auth-bg-gradient-end) 100%);
    padding: 20px;
  }

  .auth-content {
    width: 100%;
    max-width: 720px;
    margin-bottom: auto;
    margin-top: 10vh;
  }

  .auth-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .auth-title {
    font-size: 24px;
    font-weight: 600;
    color: var(--text-color-primary);
    margin-bottom: 8px;
  }

  .auth-subtitle {
    font-size: 14px;
    color: var(--text-color-secondary);
    margin: 0;
  }

  .auth-container {
    background-color: transparent;
    border-radius: 8px;
  }

  .auth-footer {
    margin-top: auto;
    padding: 20px 0;
    text-align: center;
    color: var(--text-color-secondary);
    font-size: 12px;
  }

  /* 确保子组件（登录表单等）不会超出容器 */
  :deep(.el-card) {
    max-width: 720px;
    width: 100%;
    border: none;
    border-radius: 8px;
    box-shadow: var(--auth-card-shadow);
    background-color: var(--auth-card-bg);
  }

  :deep(.el-card__header) {
    padding: 20px;
    border-bottom: 1px solid var(--border-color-light);
  }

  :deep(.el-card__body) {
    padding: 24px;
  }

  :deep(.el-form-item__label) {
    font-weight: 500;
    color: var(--text-color-primary);
  }

  :deep(.el-input__wrapper) {
    box-shadow: none;
    border: 1px solid var(--auth-input-border);
    border-radius: 4px;
    background-color: var(--bg-color);
  }

  :deep(.el-input__wrapper:hover) {
    border-color: var(--color-primary);
  }

  :deep(.el-input__wrapper.is-focus) {
    border-color: var(--color-primary);
    box-shadow: var(--auth-input-focus-shadow);
  }

  :deep(.el-button) {
    width: 100%;
    height: 40px;
    font-size: 16px;
  }

  :deep(.el-checkbox__label) {
    color: var(--text-color-regular);
  }

  :deep(.el-link) {
    font-size: 14px;
  }
</style>
