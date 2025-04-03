<template>
  <div class="layout-default">
    <el-container class="layout-container">
      <app-header
        :username="userStore.userInfo?.username"
        :is-collapsed="isCollapse"
        @toggle-sidebar="isCollapse = !isCollapse"
        @command="handleCommand"
      />

      <el-container class="main-container">
        <app-sidebar :width="sidebarWidth" :is-collapsed="isCollapse" :active-menu="activeMenu">
          <!-- 仪表盘 -->
          <el-menu-item :index="userStore.userInfo?.roles?.includes('admin') ? '/admin/dashboard' : '/dashboard'" @click="navigateToDashboard">
            <el-icon><DataBoard /></el-icon>
            <template #title>仪表盘</template>
          </el-menu-item>
          
          <!-- 运费计算 -->
          <el-sub-menu index="/calculator">
            <template #title>
              <el-icon><Operation /></el-icon>
              <span>运费计算</span>
            </template>
            <el-menu-item index="/calculator/single" @click="navigateToSingleCalculator">
              <el-icon><Tickets /></el-icon>
              <template #title>单票计算</template>
            </el-menu-item>
            <el-menu-item index="/calculator/batch" @click="navigateToBatchCalculator">
              <el-icon><Files /></el-icon>
              <template #title>批量计算</template>
            </el-menu-item>
          </el-sub-menu>
          
          <!-- 产品管理 -->
          <el-sub-menu index="/product">
            <template #title>
              <el-icon><Goods /></el-icon>
              <span>产品管理</span>
            </template>
            <el-menu-item index="/product/list">
              <el-icon><List /></el-icon>
              <template #title>产品列表</template>
            </el-menu-item>
          </el-sub-menu>
          
          <!-- 燃油费率 -->
          <el-menu-item index="/fuel-rate">
            <el-icon><Odometer /></el-icon>
            <template #title>燃油费率</template>
          </el-menu-item>
          
          <!-- 邮编管理 -->
          <el-sub-menu index="/postal">
            <template #title>
              <el-icon><MapLocation /></el-icon>
              <span>邮编管理</span>
            </template>
            <el-menu-item index="/postal/zip-zones">
              <el-icon><Location /></el-icon>
              <template #title>分区设置</template>
            </el-menu-item>
            <el-menu-item index="/postal/remote-areas">
              <el-icon><Position /></el-icon>
              <template #title>偏远地区</template>
            </el-menu-item>
          </el-sub-menu>
          
          <!-- 报表分析 -->
          <el-sub-menu index="/report">
            <template #title>
              <el-icon><TrendCharts /></el-icon>
              <span>报表分析</span>
            </template>
            <el-menu-item index="/report/usage">
              <el-icon><Histogram /></el-icon>
              <template #title>使用统计</template>
            </el-menu-item>
            <el-menu-item index="/report/cost">
              <el-icon><PieChart /></el-icon>
              <template #title>成本分析</template>
            </el-menu-item>
            <el-menu-item index="/report/export">
              <el-icon><Download /></el-icon>
              <template #title>数据导出</template>
            </el-menu-item>
          </el-sub-menu>
          
          <!-- 系统管理 -->
          <el-sub-menu index="/system">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统管理</span>
            </template>
            <el-menu-item index="/system/provider">
              <el-icon><Shop /></el-icon>
              <template #title>服务商管理</template>
            </el-menu-item>
            <el-menu-item index="/system/user">
              <el-icon><User /></el-icon>
              <template #title>用户管理</template>
            </el-menu-item>
            <el-menu-item index="/system/role">
              <el-icon><Lock /></el-icon>
              <template #title>角色权限</template>
            </el-menu-item>
            <el-menu-item index="/system/log">
              <el-icon><Notebook /></el-icon>
              <template #title>操作日志</template>
            </el-menu-item>
            <el-menu-item index="/system/data-sync">
              <el-icon><RefreshRight /></el-icon>
              <template #title>数据同步</template>
            </el-menu-item>
          </el-sub-menu>
        </app-sidebar>

        <el-main class="main">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessageBox, ElMessage } from 'element-plus';
import { 
  Operation, Files, Sort, Clock, DataBoard, Money, Setting, 
  MapLocation, TrendCharts, Goods, List, FolderOpened, PriceTag, 
  Odometer, Plus, Calendar, Location, Position, Upload,
  Histogram, PieChart, Download, User, Lock, Notebook,
  RefreshRight, Tickets, Shop
} from '@element-plus/icons-vue';
import { useUserStore } from '@/stores/user';
import { AppHeader, AppSidebar } from '@/components/common';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

// 初始化用户状态
onMounted(async () => {
  await userStore.initialize();
  if (!userStore.isLoggedIn) {
    router.push('/auth/login');
  }
});

const isCollapse = ref(false);
const activeMenu = computed(() => route.path);
const sidebarWidth = computed(() =>
  isCollapse.value ? 'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)',
);

// 导航到仪表盘
const navigateToDashboard = () => {
  const targetPath = userStore.userInfo?.roles?.includes('admin') ? '/admin/dashboard' : '/dashboard';
  router.push(targetPath);
};

// 导航到单票计算页面
const navigateToSingleCalculator = () => {
  console.log('导航到单票计算页面，当前路径:', route.path);
  try {
    // 确保路径前缀正确
    const targetPath = '/calculator/single';
    console.log('准备导航到:', targetPath);
    
    // 强制导航，避免Vue Router缓存
    window.location.href = `${window.location.origin}${targetPath}`;
  } catch (error) {
    console.error('导航错误:', error);
  }
};

// 导航到批量计算页面
const navigateToBatchCalculator = () => {
  console.log('导航到批量计算页面，当前路径:', route.path);
  try {
    // 确保路径前缀正确
    const targetPath = '/calculator/batch';
    console.log('准备导航到:', targetPath);
    
    // 强制导航，避免Vue Router缓存
    window.location.href = `${window.location.origin}${targetPath}`;
  } catch (error) {
    console.error('导航错误:', error);
  }
};

// 处理用户命令
const handleCommand = async (command: string) => {
  console.log('接收到命令:', command);
  
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm(
        '确定要退出登录吗？',
        '提示',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      );
      
      console.log('用户确认登出');
      await userStore.logout();
      ElMessage.success('已成功退出登录');
      
      // 使用更直接的方式重定向到登录页
      console.log('强制跳转到登录页');
      window.location.href = `${window.location.origin}/auth/login`;
    } catch (error) {
      console.log('用户取消登出或发生错误:', error);
    }
  } else if (command === 'profile') {
    router.push('/system/profile');
  } else if (command === 'settings') {
    router.push('/system/settings');
  }
};
</script>

<style lang="scss" scoped>
.layout-default {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  position: relative;
  background-color: var(--el-bg-color);
}

.layout-container {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.main-container {
  height: calc(100vh - var(--header-height, 60px));
  display: flex;
  overflow: hidden;
}

.main {
  flex: 1;
  padding: 20px;
  overflow-x: hidden;
  overflow-y: auto;
  background-color: var(--el-bg-color-page);
  position: relative;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
