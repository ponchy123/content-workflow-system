import { ref, shallowRef } from 'vue';
import type { ApiResponse } from '@/types/common';
import { handleError } from '@/utils/logger/error-handler';

export interface RequestOptions {
  immediate?: boolean;
  onSuccess?: (data: any) => void;
  onError?: (error: unknown) => void;
  onFinally?: () => void;
}

export function useRequest<T, P extends any[] = []>(
  requestFn: (...args: P) => Promise<ApiResponse<T>>,
  options: RequestOptions = {},
) {
  const data = ref<T | null>(null);
  const loading = ref(false);
  const error = ref<Error | null>(null);

  const execute = async (...args: P): Promise<T | null> => {
    loading.value = true;
    error.value = null;

    try {
      const response = await requestFn(...args);
      data.value = response.data;
      options.onSuccess?.(response.data);
      return response.data;
    } catch (err) {
      error.value = err as Error;
      handleError(err);
      options.onError?.(err);
      return null;
    } finally {
      loading.value = false;
      options.onFinally?.();
    }
  };

  if (options.immediate) {
    execute(...([] as unknown as P));
  }

  return {
    data,
    loading,
    error,
    execute,
  };
}

export function usePagination<T, P extends any[] = any[]>(
  requestFn: (...args: P) => Promise<ApiResponse<T>>,
  options: RequestOptions = {},
) {
  const { data, loading, error, execute } = useRequest<T, P>(requestFn, options);
  const page = ref(1);
  const pageSize = ref(10);
  const total = ref(0);

  const setPage = (newPage: number) => {
    page.value = newPage;
  };

  const setPageSize = (newPageSize: number) => {
    pageSize.value = newPageSize;
    page.value = 1; // 重置到第一页
  };

  return {
    data,
    loading,
    error,
    execute,
    page,
    pageSize,
    total,
    setPage,
    setPageSize,
  };
}
