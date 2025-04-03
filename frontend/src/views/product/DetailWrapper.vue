<template>
  <div>
    <Suspense>
      <template #default>
        <ProductDetail :id="+productId" />
      </template>
      <template #fallback>
        <div class="loading-container">
          <el-skeleton :rows="10" animated />
          <div class="loading-text">正在加载产品详情...</div>
        </div>
      </template>
    </Suspense>
  </div>
</template>

<script setup lang="ts">
import { defineAsyncComponent, computed, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const productId = computed(() => route.params.id);
const ProductDetail = defineAsyncComponent(() => import('./detail.vue'));

// 定义onUnmounted钩子，避免未定义警告
const onNodeUnmounted = () => {
  console.log('DetailWrapper组件已卸载');
};

onUnmounted(onNodeUnmounted);
</script>

<style scoped>
.loading-container {
  padding: 20px;
}

.loading-text {
  text-align: center;
  margin-top: 20px;
  color: #909399;
  font-size: 14px;
}
</style> 