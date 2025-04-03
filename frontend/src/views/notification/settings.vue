<template>
  <div class="notification-settings">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>通知设置</span>
        </div>
      </template>

      <el-form ref="formRef" :model="settings" :rules="rules" label-width="120px">
        <el-form-item label="通知数量限制" prop="maxCount">
          <el-input-number v-model="settings.maxCount" :min="10" :max="100" :step="10" />
          <div class="form-item-tip">超过限制的通知将自动清理</div>
        </el-form-item>

        <el-form-item label="通知保留天数" prop="expirationDays">
          <el-input-number v-model="settings.expirationDays" :min="1" :max="30" :step="1" />
          <div class="form-item-tip">超过天数的通知将自动清理</div>
        </el-form-item>

        <el-form-item label="声音提醒" prop="soundEnabled">
          <el-switch v-model="settings.soundEnabled" />
          <div class="form-item-tip">收到新通知时播放提示音</div>
        </el-form-item>

        <el-form-item label="桌面通知" prop="desktopNotification">
          <el-switch
            v-model="settings.desktopNotification"
            :disabled="!isDesktopNotificationSupported || !hasPermission"
            @change="handleDesktopNotificationChange"
          />
          <div class="form-item-tip">
            <template v-if="!isDesktopNotificationSupported"> 您的浏览器不支持桌面通知 </template>
            <template v-else-if="!hasPermission">
              需要授权才能开启桌面通知
              <el-button type="primary" link @click="requestPermission"> 点击授权 </el-button>
            </template>
            <template v-else> 在系统托盘显示通知提醒 </template>
          </div>
        </el-form-item>

        <el-form-item label="按模块分组" prop="groupByModule">
          <el-switch v-model="settings.groupByModule" />
          <div class="form-item-tip">通知列表按模块分组显示</div>
        </el-form-item>

        <el-form-item label="自动清理" prop="autoCleanup">
          <el-switch v-model="settings.autoCleanup" />
          <div class="form-item-tip">自动清理过期和超量的通知</div>
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
  import { ref, onMounted } from 'vue';
  import { ElMessage } from 'element-plus';
  import type { FormInstance, FormRules } from 'element-plus';
  import type { NotificationConfig } from '@/types/notification';
  import { useNotificationStore } from '@/stores/notification/notification';

  const notificationStore = useNotificationStore();
  const formRef = ref<FormInstance>();

  const settings = ref<NotificationConfig>({
    maxCount: 50,
    expirationDays: 7,
    soundEnabled: true,
    desktopNotification: false,
    groupByModule: false,
    autoCleanup: true,
  });

  const rules: FormRules = {
    maxCount: [
      { required: true, message: '请设置通知数量限制', trigger: 'blur' },
      { type: 'number', min: 10, max: 100, message: '数量限制必须在10-100之间', trigger: 'blur' },
    ],
    expirationDays: [
      { required: true, message: '请设置通知保留天数', trigger: 'blur' },
      { type: 'number', min: 1, max: 30, message: '保留天数必须在1-30之间', trigger: 'blur' },
    ],
  };

  const isDesktopNotificationSupported = ref(false);
  const hasPermission = ref(false);

  const checkNotificationSupport = () => {
    isDesktopNotificationSupported.value = 'Notification' in window;
    if (isDesktopNotificationSupported.value) {
      hasPermission.value = Notification.permission === 'granted';
    }
  };

  const requestPermission = async () => {
    try {
      const permission = await Notification.requestPermission();
      hasPermission.value = permission === 'granted';
      if (hasPermission.value) {
        settings.value.desktopNotification = true;
        ElMessage.success('授权成功');
      } else {
        ElMessage.warning('您拒绝了通知权限');
      }
    } catch (error) {
      console.error('Failed to request notification permission:', error);
      ElMessage.error('请求授权失败');
    }
  };

  const handleDesktopNotificationChange = (value: string | number | boolean) => {
    if (value && !hasPermission.value) {
      settings.value.desktopNotification = false;
      requestPermission();
    }
  };

  const handleSave = async () => {
    if (!formRef.value) return;

    await formRef.value.validate(async valid => {
      if (valid) {
        try {
          await notificationStore.updateSettings(settings.value);
          ElMessage.success('设置已保存');
        } catch (error) {
          console.error('Failed to save settings:', error);
          ElMessage.error('保存失败');
        }
      }
    });
  };

  const handleReset = () => {
    if (!formRef.value) return;
    formRef.value.resetFields();
  };

  const loadSettings = async () => {
    try {
      const config = await notificationStore.getSettings();
      settings.value = { ...config };
    } catch (error) {
      console.error('Failed to load settings:', error);
      ElMessage.error('加载设置失败');
    }
  };

  onMounted(() => {
    checkNotificationSupport();
    loadSettings();
  });
</script>

<style scoped>
  .notification-settings {
    padding: 20px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .form-item-tip {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-top: 4px;
    line-height: 1.4;
  }

  :deep(.el-input-number) {
    width: 160px;
  }
</style>
