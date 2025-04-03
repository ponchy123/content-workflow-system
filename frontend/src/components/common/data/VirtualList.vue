<template>
  <div
    ref="containerRef"
    class="virtual-list"
    :style="{ height: height + 'px' }"
    @scroll="handleScroll"
  >
    <div class="virtual-list__phantom" :style="{ height: totalHeight + 'px' }" />
    <div class="virtual-list__content" :style="{ transform: `translateY(${startOffset}px)` }">
      <div
        v-for="item in visibleData"
        :key="item[itemKey]"
        class="virtual-list__item"
        :style="{ height: itemHeight + 'px' }"
      >
        <slot :item="item" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, onMounted, onBeforeUnmount } from 'vue';

  interface Props {
    data: any[];
    itemHeight: number;
    height: number;
    itemKey?: string;
    bufferSize?: number;
  }

  const props = withDefaults(defineProps<Props>(), {
    data: () => [],
    itemHeight: 50,
    height: 400,
    itemKey: 'id',
    bufferSize: 5,
  });

  const containerRef = ref<HTMLElement>();
  const scrollTop = ref(0);

  // 计算总高度
  const totalHeight = computed(() => {
    return props.data.length * props.itemHeight;
  });

  // 计算可见区域的起始索引
  const startIndex = computed(() => {
    return Math.floor(scrollTop.value / props.itemHeight);
  });

  // 计算可见区域的结束索引
  const endIndex = computed(() => {
    const visibleCount = Math.ceil(props.height / props.itemHeight);
    return Math.min(startIndex.value + visibleCount + props.bufferSize, props.data.length);
  });

  // 计算可见区域的偏移量
  const startOffset = computed(() => {
    return Math.max(0, startIndex.value - props.bufferSize) * props.itemHeight;
  });

  // 计算可见区域的数据
  const visibleData = computed(() => {
    const start = Math.max(0, startIndex.value - props.bufferSize);
    return props.data.slice(start, endIndex.value);
  });

  // 处理滚动事件
  const handleScroll = () => {
    if (containerRef.value) {
      scrollTop.value = containerRef.value.scrollTop;
    }
  };

  // 监听滚动事件
  onMounted(() => {
    containerRef.value?.addEventListener('scroll', handleScroll);
  });

  onBeforeUnmount(() => {
    containerRef.value?.removeEventListener('scroll', handleScroll);
  });
</script>

<style>
  .virtual-list {
    position: relative;
    overflow-y: auto;
  }

  .virtual-list__phantom {
    position: absolute;
    left: 0;
    top: 0;
    right: 0;
    z-index: -1;
  }

  .virtual-list__content {
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    will-change: transform;
  }

  .virtual-list__item {
    box-sizing: border-box;
  }
</style>
