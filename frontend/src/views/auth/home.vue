<template>
  <div class="home-container">
    <h1>物流运费订单计算系统</h1>
    <p class="welcome-text">欢迎使用运费计算平台</p>
    
    <el-row :gutter="20" class="feature-cards">
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <h2>快速计算</h2>
            </div>
          </template>
          <div class="card-content">
            <p>输入包裹信息，获取即时运费报价</p>
            <el-button type="primary" @click="goToCalculator">开始计算</el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <h2>批量导入</h2>
            </div>
          </template>
          <div class="card-content">
            <p>批量处理多个运单，提高效率</p>
            <el-button type="primary" @click="goToBatchImport">批量导入</el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <h2>查看报告</h2>
            </div>
          </template>
          <div class="card-content">
            <p>查看历史计算记录和统计报告</p>
            <el-button type="primary" @click="goToReports">查看报告</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();

const goToCalculator = () => {
  router.push('/calculator');
};

const goToBatchImport = () => {
  router.push('/calculator/batch');
};

const goToReports = () => {
  router.push('/reports');
};
</script>

<style scoped>
.home-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

h1 {
  font-size: 32px;
  margin-bottom: 16px;
  color: var(--el-color-primary);
  text-align: center;
}

.welcome-text {
  font-size: 18px;
  color: var(--el-text-color-secondary);
  text-align: center;
  margin-bottom: 40px;
}

.feature-cards {
  margin-top: 30px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  font-size: 18px;
  margin: 0;
}

.card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  min-height: 120px;
  justify-content: space-between;
}

.card-content p {
  text-align: center;
  color: var(--el-text-color-regular);
}
</style> 