<template>
  <div class="profile-view">
    <div class="page-header">
      <h1 class="page-title">个人信息</h1>
    </div>

    <div class="profile-container">
      <el-card class="profile-card">
        <template #header>
          <div class="card-header">
            <h3>个人信息</h3>
          </div>
        </template>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="100px"
          class="profile-form"
        >
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" disabled />
          </el-form-item>

          <el-form-item label="昵称" prop="nickname">
            <el-input v-model="form.nickname" />
          </el-form-item>

          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" type="email" />
          </el-form-item>

          <el-form-item label="手机号" prop="phone">
            <el-input v-model="form.phone" />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="handleSubmit">保存修改</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card class="profile-card">
        <template #header>
          <div class="card-header">
            <h3>修改密码</h3>
          </div>
        </template>

        <el-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          label-width="100px"
          class="password-form"
        >
          <el-form-item label="当前密码" prop="oldPassword">
            <el-input v-model="passwordForm.oldPassword" type="password" show-password />
          </el-form-item>

          <el-form-item label="新密码" prop="newPassword">
            <el-input v-model="passwordForm.newPassword" type="password" show-password />
          </el-form-item>

          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="handlePasswordChange"> 修改密码 </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted } from 'vue';
  import { ElMessage } from 'element-plus';
  import type { FormInstance, FormRules } from 'element-plus';
  import { useUserStore } from '@/stores/user';
  import { updateUser } from '@/api/users/users';
  import { changePassword } from '@/api/users/auth';

  const userStore = useUserStore();
  const formRef = ref<FormInstance>();
  const passwordFormRef = ref<FormInstance>();

  const form = ref({
    username: '',
    nickname: '',
    email: '',
    phone: '',
  });

  const passwordForm = ref({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const rules: FormRules = {
    nickname: [
      { required: true, message: '请输入昵称', trigger: 'blur' },
      { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' },
    ],
    email: [
      { required: true, message: '请输入邮箱地址', trigger: 'blur' },
      { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
    ],
    phone: [
      { required: true, message: '请输入手机号', trigger: 'blur' },
      { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
    ],
  };

  const passwordRules: FormRules = {
    oldPassword: [
      { required: true, message: '请输入当前密码', trigger: 'blur' },
      { min: 6, message: '密码长度不能小于6位', trigger: 'blur' },
    ],
    newPassword: [
      { required: true, message: '请输入新密码', trigger: 'blur' },
      { min: 6, message: '密码长度不能小于6位', trigger: 'blur' },
    ],
    confirmPassword: [
      { required: true, message: '请再次输入新密码', trigger: 'blur' },
      {
        validator: (rule: any, value: string, callback: Function) => {
          if (value !== passwordForm.value.newPassword) {
            callback(new Error('两次输入密码不一致'));
          } else {
            callback();
          }
        },
        trigger: 'blur',
      },
    ],
  };

  const handleSubmit = async () => {
    if (!formRef.value) return;

    await formRef.value.validate(async valid => {
      if (valid) {
        try {
          await updateUser(userStore.userInfo!.id.toString(), {
            nickname: form.value.nickname,
            email: form.value.email,
            phone: form.value.phone,
          });
          ElMessage.success('个人信息更新成功');
          // 刷新用户信息
          await userStore.refreshUserInfo();
        } catch (error: any) {
          ElMessage.error(error.message || '更新失败');
        }
      }
    });
  };

  const handlePasswordChange = async () => {
    if (!passwordFormRef.value) return;

    await passwordFormRef.value.validate(async valid => {
      if (valid) {
        try {
          await changePassword(userStore.userInfo!.id.toString(), {
            old_password: passwordForm.value.oldPassword,
            new_password: passwordForm.value.newPassword,
            confirm_password: passwordForm.value.confirmPassword
          });
          ElMessage.success('密码修改成功');
          passwordForm.value = {
            oldPassword: '',
            newPassword: '',
            confirmPassword: '',
          };
        } catch (error: any) {
          ElMessage.error(error.message || '密码修改失败');
        }
      }
    });
  };

  onMounted(async () => {
    // 从store中直接获取用户信息
    const currentUserInfo = userStore.userInfo;
    if (currentUserInfo) {
      form.value = {
        username: currentUserInfo.username || '',
        nickname: currentUserInfo.nickname || '',
        email: currentUserInfo.email || '',
        phone: currentUserInfo.phone || ''
      };
    } else {
      ElMessage.warning('无法获取用户信息');
    }
  });
</script>

<style scoped>
  .profile-view {
    padding: var(--spacing-large);

    .page-header {
      margin-bottom: var(--spacing-large);

      .page-title {
        font-size: var(--font-size-extra-large);
        font-weight: var(--font-weight-bold);
        color: var(--text-color-primary);
        margin-bottom: var(--spacing-base);
      }
    }

    .profile-container {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: var(--spacing-large);

      @media (max-width: 768px) {
        grid-template-columns: 1fr;
      }

      .profile-card {
        background-color: var(--bg-color);
        border-radius: var(--border-radius-base);
        box-shadow: var(--box-shadow-light);
        padding: var(--spacing-large);

        .avatar-section {
          text-align: center;
          margin-bottom: var(--spacing-large);

          .avatar-wrapper {
            width: 120px;
            height: 120px;
            margin: 0 auto var(--spacing-base);
            position: relative;

            .avatar {
              width: 100%;
              height: 100%;
              border-radius: 50%;
              object-fit: cover;
              border: 2px solid var(--border-color);
            }

            .upload-overlay {
              position: absolute;
              bottom: 0;
              left: 0;
              right: 0;
              background-color: var(--bg-color-overlay);
              padding: var(--spacing-mini);
              color: var(--text-color-regular);
              font-size: var(--font-size-small);
              cursor: pointer;
              opacity: 0;
              transition: opacity var(--transition-duration) var(--transition-function);

              &:hover {
                opacity: 1;
              }
            }
          }

          .user-name {
            font-size: var(--font-size-large);
            font-weight: var(--font-weight-medium);
            color: var(--text-color-primary);
            margin-bottom: var(--spacing-mini);
          }

          .user-role {
            font-size: var(--font-size-base);
            color: var(--text-color-secondary);
          }
        }

        .info-list {
          .info-item {
            display: flex;
            align-items: center;
            padding: var(--spacing-base) 0;
            border-bottom: 1px solid var(--border-color-light);

            &:last-child {
              border-bottom: none;
            }

            .item-label {
              width: 80px;
              color: var(--text-color-secondary);
              font-size: var(--font-size-base);
            }

            .item-value {
              flex: 1;
              color: var(--text-color-primary);
              font-size: var(--font-size-base);
            }
          }
        }
      }

      .profile-content {
        background-color: var(--bg-color);
        border-radius: var(--border-radius-base);
        box-shadow: var(--box-shadow-light);
        padding: var(--spacing-large);

        .section-title {
          font-size: var(--font-size-large);
          font-weight: var(--font-weight-medium);
          color: var(--text-color-primary);
          margin-bottom: var(--spacing-large);
          padding-bottom: var(--spacing-base);
          border-bottom: 1px solid var(--border-color);
        }

        .profile-form {
          max-width: 600px;

          :deep(.el-form-item) {
            margin-bottom: var(--spacing-large);

            .el-form-item__label {
              font-weight: var(--font-weight-medium);
              color: var(--text-color-regular);
            }
          }
        }

        .form-actions {
          margin-top: var(--spacing-extra-large);
          padding-top: var(--spacing-large);
          border-top: 1px solid var(--border-color);
          display: flex;
          justify-content: flex-end;
          gap: var(--spacing-base);
        }
      }
    }
  }
</style>
