<template>
  <div class="layout-admin">
    <el-container class="layout-container">
      <app-header
        :title="'系统管理'"
        :username="userStore.userInfo?.username"
        :is-collapsed="isCollapse"
        @toggle-sidebar="isCollapse = !isCollapse"
        @command="handleCommand"
      />

      <el-container class="main-container">
        <app-sidebar :width="sidebarWidth" :is-collapsed="isCollapse" :active-menu="activeMenu">
          <el-menu-item index="/admin/dashboard">
            <el-icon><data-line /></el-icon>
            <template #title>仪表盘</template>
          </el-menu-item>
          <el-menu-item index="/admin/products">
            <el-icon><box /></el-icon>
            <template #title>产品管理</template>
          </el-menu-item>
          <el-menu-item index="/admin/rates">
            <el-icon><money /></el-icon>
            <template #title>费率管理</template>
          </el-menu-item>
          <el-menu-item index="/admin/postal">
            <el-icon><location /></el-icon>
            <template #title>邮编管理</template>
          </el-menu-item>
          <el-menu-item index="/admin/users">
            <el-icon><user /></el-icon>
            <template #title>用户管理</template>
          </el-menu-item>
          <el-menu-item index="/admin/settings">
            <el-icon><setting /></el-icon>
            <template #title>系统设置</template>
          </el-menu-item>
        </app-sidebar>

        <el-main class="main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed } from 'vue';
  import { useRouter, useRoute } from 'vue-router';
  import { ElMessageBox } from 'element-plus';
  import { DataLine, Box, Money, Location, User, Setting } from '@element-plus/icons-vue';
  import { useUserStore } from '@/stores/user';
  import { AppHeader, AppSidebar } from '@/components/common';

  const router = useRouter();
  const route = useRoute();
  const userStore = useUserStore();

  const isCollapse = ref(false);
  const activeMenu = computed(() => route.path);
  const sidebarWidth = computed(() =>
    isCollapse.value ? 'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)',
  );

  const handleCommand = async (command: string) => {
    switch (command) {
      case 'settings':
        router.push('/admin/profile');
        break;
      case 'logout':
        try {
          await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          });
          userStore.logout();
          router.push('/auth/login');
        } catch {
          // 用户取消操作
        }
        break;
    }
  };
</script>
