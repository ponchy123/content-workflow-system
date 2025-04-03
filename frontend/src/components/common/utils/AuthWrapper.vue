<template>
  <div v-if="hasPermission" class="auth-wrapper" :class="{ 'is-disabled': disabled }">
    <slot />
  </div>
  <template v-else-if="$slots.fallback">
    <slot name="fallback" />
  </template>
</template>

<script setup lang="ts">
  import { computed } from 'vue';
  import { usePermission } from '@/composables/usePermission';

  interface Props {
    permission?: string | string[];
    disabled?: boolean;
    mode?: 'all' | 'any';
  }

  const props = withDefaults(defineProps<Props>(), {
    mode: 'all',
    disabled: false,
  });

  const { checkPermission } = usePermission();

  // 检查是否有权限
  const hasPermission = computed(() => {
    if (!props.permission) return true;

    const permissions = Array.isArray(props.permission) ? props.permission : [props.permission];

    if (props.mode === 'all') {
      return permissions.every(p => checkPermission(p));
    }
    return permissions.some(p => checkPermission(p));
  });
</script>

<style>
  .auth-wrapper {
    display: contents;
  }

  .auth-wrapper.is-disabled {
    cursor: not-allowed;
    opacity: 0.5;
    pointer-events: none;
  }
</style>
