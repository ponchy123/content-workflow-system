<template>
  <aside class="app-sidebar" :class="{ 'is-collapsed': collapsed }">
    <!-- 侧边栏菜单 -->
    <el-menu
      :default-active="activeMenu"
      :collapse="collapsed"
      :unique-opened="uniqueOpened"
      :collapse-transition="collapseTransition"
      :router="true"
      class="app-sidebar__menu"
      @select="handleMenuSelect"
    >
      <slot />
    </el-menu>

    <!-- 侧边栏底部 -->
    <div v-if="$slots.footer" class="app-sidebar__footer">
      <slot name="footer" />
    </div>
  </aside>
</template>

<script setup lang="ts">
  import { useRouter } from 'vue-router';

  interface Props {
    collapsed?: boolean;
    activeMenu?: string;
    uniqueOpened?: boolean;
    collapseTransition?: boolean;
    router?: boolean;
    width?: string;
    isCollapsed?: boolean;
  }

  const router = useRouter();

  const props = withDefaults(defineProps<Props>(), {
    collapsed: false,
    activeMenu: '',
    uniqueOpened: true,
    collapseTransition: true,
    router: true,
    width: '240px',
    isCollapsed: false,
  });

  // 确保菜单项的点击事件能够正确处理
  const handleMenuClick = (route: string) => {
    console.log('处理菜单点击事件，路由:', route);
    router.push(route);
  };
  
  // 处理菜单选择事件
  const handleMenuSelect = (index: string) => {
    console.log('菜单选择事件，index:', index);
    if (index && index.startsWith('/')) {
      router.push(index);
    }
  };

  defineExpose({
    handleMenuClick,
    handleMenuSelect
  });
</script>

<style lang="scss" scoped>
.app-sidebar {
  display: flex;
  flex-direction: column;
  width: var(--sidebar-width, 240px);
  height: 100%;
  background-color: var(--sidebar-menu-bg, #fff);
  transition: width var(--transition-duration, 0.3s) var(--transition-timing-function, ease);
  position: fixed;
  left: 0;
  top: 0;
  z-index: var(--z-index-sidebar, 1000);
  box-shadow: 1px 0 8px rgba(0, 0, 0, 0.08);

  &.is-collapsed {
    width: var(--sidebar-collapsed-width, 64px);
  }

  :deep(.el-menu) {
    border-right: none;
    user-select: none;
    background-color: transparent;
  }

  :deep(.el-menu--collapse) {
    width: var(--sidebar-collapsed-width, 64px);
  }

  :deep(.el-menu-item) {
    height: var(--sidebar-menu-item-height, 50px);
    line-height: var(--sidebar-menu-item-height, 50px);
    
    &.is-active {
      background-color: var(--sidebar-menu-active-bg, rgba(64, 158, 255, 0.1));
      border-right: 3px solid var(--el-color-primary);
    }

    &:hover {
      background-color: var(--sidebar-menu-hover-bg, rgba(64, 158, 255, 0.05));
    }
  }

  :deep(.el-sub-menu__title) {
    height: var(--sidebar-menu-item-height, 50px);
    line-height: var(--sidebar-menu-item-height, 50px);
    
    &:hover {
      background-color: var(--sidebar-menu-hover-bg, rgba(64, 158, 255, 0.05));
    }
  }

  :deep(.el-sub-menu.is-active .el-sub-menu__title) {
    color: var(--el-color-primary);
  }

  :deep(.el-sub-menu) {
    .el-menu {
      background-color: var(--sidebar-submenu-bg, rgba(0, 0, 0, 0.02));
    }
  }

  :deep(.el-icon) {
    margin-right: 10px;
    font-size: 18px;
    vertical-align: middle;
  }

  &__menu {
    flex: 1;
    overflow-x: hidden;
    overflow-y: auto;
    margin-top: var(--header-height, 60px);
    padding: 10px 0;

    &::-webkit-scrollbar {
      width: 4px;
      height: 4px;
    }

    &::-webkit-scrollbar-thumb {
      background: var(--el-border-color-lighter);
      border-radius: 10px;
    }

    &::-webkit-scrollbar-track {
      background: transparent;
    }
  }

  &__footer {
    height: 40px;
    line-height: 40px;
    padding: 0 16px;
    border-top: 1px solid var(--sidebar-border-color, #f0f0f0);
    overflow: hidden;
  }
}

// 暗色主题支持
.dark {
  .app-sidebar {
    background-color: var(--el-bg-color-overlay);
    border-color: var(--el-border-color-extra-light);

    :deep(.el-menu-item) {
      &.is-active {
        background-color: var(--el-color-primary-dark-2);
      }
    }
    
    :deep(.el-sub-menu) {
      .el-menu {
        background-color: rgba(0, 0, 0, 0.2);
      }
    }
  }
}
</style>
