<!-- 邮编管理主页 -->
<template>
  <div class="postal-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>邮编管理系统</span>
        </div>
      </template>
      
      <p>请从左侧菜单选择需要管理的功能：</p>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card shadow="hover" @click="navigateTo('ZipZones')">
            <template #header>
              <div class="module-header">
                <el-icon><grid /></el-icon>
                <span>邮编分区</span>
              </div>
            </template>
            <div class="module-content">
              管理邮编分区信息，设置始发地与目的地邮编对应的分区号。
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <el-card shadow="hover" @click="navigateTo('RemoteAreas')">
            <template #header>
              <div class="module-header">
                <el-icon><place /></el-icon>
                <span>偏远地区</span>
              </div>
            </template>
            <div class="module-content">
              管理偏远地区邮编，设置偏远地区的等级以便于计算附加费。
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { Grid, Place } from '@element-plus/icons-vue';

const router = useRouter();

const navigateTo = (routeName: string) => {
  router.push({ name: routeName });
};
</script>

<style scoped>
.postal-management {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  font-weight: bold;
  font-size: 18px;
}

.module-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}

.module-content {
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
  height: 80px;
}

.el-card {
  cursor: pointer;
  transition: all 0.3s;
  height: 100%;
}

.el-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}
</style>
