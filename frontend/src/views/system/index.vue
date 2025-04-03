<template>
  <div class="system-settings">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>系统设置</h2>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <!-- 基本设置 -->
        <el-tab-pane label="基本设置" name="basic">
          <el-form ref="basicFormRef" :model="basicForm" :rules="basicRules" label-width="120px">
            <el-form-item label="系统名称" prop="systemName">
              <el-input v-model="basicForm.systemName" />
            </el-form-item>
            <el-form-item label="公司名称" prop="companyName">
              <el-input v-model="basicForm.companyName" />
            </el-form-item>
            <el-form-item label="联系电话" prop="contactPhone">
              <el-input v-model="basicForm.contactPhone" />
            </el-form-item>
            <el-form-item label="联系邮箱" prop="contactEmail">
              <el-input v-model="basicForm.contactEmail" />
            </el-form-item>
            <el-form-item label="系统Logo" prop="logo">
              <el-upload
                class="avatar-uploader"
                action="/api/system/upload"
                :show-file-list="false"
                :on-success="handleLogoSuccess"
                :before-upload="beforeLogoUpload"
              >
                <img v-if="basicForm.logo" :src="basicForm.logo" class="avatar" />
                <el-icon v-else class="avatar-uploader-icon"><plus /></el-icon>
              </el-upload>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 计算设置 -->
        <el-tab-pane label="计算设置" name="calculation">
          <el-form ref="calcFormRef" :model="calcForm" :rules="calcRules" label-width="120px">
            <el-form-item label="默认重量单位" prop="defaultWeightUnit">
              <el-select v-model="calcForm.defaultWeightUnit">
                <el-option label="千克(KG)" value="KG" />
                <el-option label="磅(LB)" value="LB" />
              </el-select>
            </el-form-item>
            <el-form-item label="默认尺寸单位" prop="defaultDimUnit">
              <el-select v-model="calcForm.defaultDimUnit">
                <el-option label="厘米(CM)" value="CM" />
                <el-option label="英寸(IN)" value="IN" />
              </el-select>
            </el-form-item>
            <el-form-item label="默认货币" prop="defaultCurrency">
              <el-select v-model="calcForm.defaultCurrency">
                <el-option label="人民币(CNY)" value="CNY" />
                <el-option label="美元(USD)" value="USD" />
              </el-select>
            </el-form-item>
            <el-form-item label="体积重系数" prop="dimFactor">
              <el-input-number v-model="calcForm.dimFactor" :min="1" :precision="2" :step="0.01" />
            </el-form-item>
            <el-form-item label="最小计费重量" prop="minChargeWeight">
              <el-input-number
                v-model="calcForm.minChargeWeight"
                :min="0.01"
                :precision="2"
                :step="0.01"
              />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 通知设置 -->
        <el-tab-pane label="通知设置" name="notification">
          <el-form ref="notifyFormRef" :model="notifyForm" :rules="notifyRules" label-width="120px">
            <el-form-item label="邮件通知" prop="emailNotification">
              <el-switch v-model="notifyForm.emailNotification" />
            </el-form-item>
            <el-form-item label="SMTP服务器" prop="smtpServer" v-if="notifyForm.emailNotification">
              <el-input v-model="notifyForm.smtpServer" />
            </el-form-item>
            <el-form-item label="SMTP端口" prop="smtpPort" v-if="notifyForm.emailNotification">
              <el-input-number v-model="notifyForm.smtpPort" :min="1" :max="65535" />
            </el-form-item>
            <el-form-item label="发件人邮箱" prop="senderEmail" v-if="notifyForm.emailNotification">
              <el-input v-model="notifyForm.senderEmail" />
            </el-form-item>
            <el-form-item label="邮箱密码" prop="emailPassword" v-if="notifyForm.emailNotification">
              <el-input v-model="notifyForm.emailPassword" type="password" show-password />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- API设置 -->
        <el-tab-pane label="API设置" name="api">
          <el-form ref="apiFormRef" :model="apiForm" :rules="apiRules" label-width="120px">
            <el-form-item label="API访问控制" prop="apiAccessControl">
              <el-switch v-model="apiForm.apiAccessControl" />
            </el-form-item>
            <el-form-item label="API密钥" prop="apiKey" v-if="apiForm.apiAccessControl">
              <el-input v-model="apiForm.apiKey" readonly>
                <template #append>
                  <el-button @click="generateApiKey">重新生成</el-button>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item label="IP白名单" prop="ipWhitelist" v-if="apiForm.apiAccessControl">
              <el-select
                v-model="apiForm.ipWhitelist"
                multiple
                filterable
                allow-create
                default-first-option
                placeholder="请输入IP地址，回车确认"
              >
                <el-option v-for="ip in apiForm.ipWhitelist" :key="ip" :label="ip" :value="ip" />
              </el-select>
            </el-form-item>
            <el-form-item label="请求频率限制" prop="rateLimit" v-if="apiForm.apiAccessControl">
              <el-input-number v-model="apiForm.rateLimit" :min="1" :step="10" />
              <span class="ml-2">次/分钟</span>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <!-- 保存按钮 -->
      <div class="actions">
        <el-button type="primary" @click="handleSave">保存设置</el-button>
        <el-button @click="handleReset">重置</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive } from 'vue';
  import { ElMessage } from 'element-plus';
  import { Plus } from '@element-plus/icons-vue';
  import type { FormInstance, FormRules } from 'element-plus';

  // 当前激活的标签页
  const activeTab = ref('basic');

  // 基本设置表单
  const basicFormRef = ref<FormInstance>();
  const basicForm = reactive({
    systemName: '',
    companyName: '',
    contactPhone: '',
    contactEmail: '',
    logo: '',
  });

  const basicRules: FormRules = {
    systemName: [
      { required: true, message: '请输入系统名称', trigger: 'blur' },
      { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' },
    ],
    companyName: [{ required: true, message: '请输入公司名称', trigger: 'blur' }],
    contactPhone: [{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }],
    contactEmail: [{ type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }],
  };

  // 计算设置表单
  const calcFormRef = ref<FormInstance>();
  const calcForm = reactive({
    defaultWeightUnit: 'KG',
    defaultDimUnit: 'CM',
    defaultCurrency: 'CNY',
    dimFactor: 139.0,
    minChargeWeight: 0.5,
  });

  const calcRules: FormRules = {
    defaultWeightUnit: [{ required: true, message: '请选择默认重量单位', trigger: 'change' }],
    defaultDimUnit: [{ required: true, message: '请选择默认尺寸单位', trigger: 'change' }],
    defaultCurrency: [{ required: true, message: '请选择默认货币', trigger: 'change' }],
    dimFactor: [{ required: true, message: '请输入体积重系数', trigger: 'blur' }],
    minChargeWeight: [{ required: true, message: '请输入最小计费重量', trigger: 'blur' }],
  };

  // 通知设置表单
  const notifyFormRef = ref<FormInstance>();
  const notifyForm = reactive({
    emailNotification: false,
    smtpServer: '',
    smtpPort: 587,
    senderEmail: '',
    emailPassword: '',
  });

  const notifyRules: FormRules = {
    smtpServer: [{ required: true, message: '请输入SMTP服务器地址', trigger: 'blur' }],
    smtpPort: [{ required: true, message: '请输入SMTP端口', trigger: 'blur' }],
    senderEmail: [
      { required: true, message: '请输入发件人邮箱', trigger: 'blur' },
      { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
    ],
    emailPassword: [{ required: true, message: '请输入邮箱密码', trigger: 'blur' }],
  };

  // API设置表单
  const apiFormRef = ref<FormInstance>();
  const apiForm = reactive({
    apiAccessControl: false,
    apiKey: '',
    ipWhitelist: [] as string[],
    rateLimit: 60,
  });

  const apiRules: FormRules = {
    apiKey: [{ required: true, message: '请生成API密钥', trigger: 'blur' }],
    rateLimit: [{ required: true, message: '请设置请求频率限制', trigger: 'blur' }],
  };

  // Logo上传相关方法
  const handleLogoSuccess = (res: any) => {
    basicForm.logo = res.url;
  };

  const beforeLogoUpload = (file: File) => {
    const isImage = file.type.startsWith('image/');
    const isLt2M = file.size / 1024 / 1024 < 2;

    if (!isImage) {
      ElMessage.error('上传文件只能是图片格式!');
      return false;
    }
    if (!isLt2M) {
      ElMessage.error('上传图片大小不能超过 2MB!');
      return false;
    }
    return true;
  };

  // 生成API密钥
  const generateApiKey = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let key = '';
    for (let i = 0; i < 32; i++) {
      key += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    apiForm.apiKey = key;
  };

  // 保存设置
  const handleSave = async () => {
    // 根据当前激活的标签页验证对应的表单
    const formRefs = {
      basic: basicFormRef,
      calculation: calcFormRef,
      notification: notifyFormRef,
      api: apiFormRef,
    };

    const currentFormRef = formRefs[activeTab.value as keyof typeof formRefs];
    if (!currentFormRef?.value) return;

    try {
      await currentFormRef.value.validate();
      // TODO: 实现保存逻辑
      ElMessage.success('保存成功');
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  // 重置设置
  const handleReset = () => {
    const formRefs = {
      basic: basicFormRef,
      calculation: calcFormRef,
      notification: notifyFormRef,
      api: apiFormRef,
    };

    const currentFormRef = formRefs[activeTab.value as keyof typeof formRefs];
    if (currentFormRef?.value) {
      currentFormRef.value.resetFields();
    }
  };
</script>

<style scoped>
  .system-settings {
    padding: 20px;
  }

  .card-header {
    margin-bottom: 20px;
  }

  .actions {
    margin-top: 20px;
    text-align: center;
  }

  .avatar-uploader {
    text-align: center;
  }

  .avatar-uploader .avatar {
    width: 178px;
    height: 178px;
    display: block;
  }

  .avatar-uploader .el-upload {
    border: 1px dashed var(--el-border-color);
    border-radius: 6px;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: var(--el-transition-duration-fast);
  }

  .avatar-uploader .el-upload:hover {
    border-color: var(--el-color-primary);
  }

  .avatar-uploader-icon {
    font-size: 28px;
    color: #8c939d;
    width: 178px;
    height: 178px;
    text-align: center;
    line-height: 178px;
  }

  .ml-2 {
    margin-left: 8px;
  }
</style>
