import { ref, reactive, watch } from 'vue';
import type { Ref } from 'vue';

export interface TablePagination {
  current: number;
  pageSize: number;
  total: number;
  pageSizes?: number[];
  layout?: string;
  background?: boolean;
}

export interface TableOptions {
  autoLoad?: boolean;
  defaultPageSize?: number;
  pageSizes?: number[];
  paginationLayout?: string;
  paginationBackground?: boolean;
}

export interface TableSortParams {
  prop: string;
  order: 'ascending' | 'descending' | null;
}

export interface TableFilterParams {
  [key: string]: any;
}

export function useTable<T = any>(
  fetchDataFn: (params: any) => Promise<{ data: T[]; total: number }>,
  options: TableOptions = {}
) {
  // 默认选项
  const defaultOptions: TableOptions = {
    autoLoad: true,
    defaultPageSize: 10,
    pageSizes: [10, 20, 50, 100],
    paginationLayout: 'total, sizes, prev, pager, next, jumper',
    paginationBackground: true,
  };

  // 合并选项
  const mergedOptions = { ...defaultOptions, ...options };

  // 表格数据状态
  const tableData = ref<T[]>([]) as Ref<T[]>;
  const loading = ref(false);
  const error = ref<Error | null>(null);

  // 分页配置
  const pagination = reactive<TablePagination>({
    current: 1,
    pageSize: mergedOptions.defaultPageSize!,
    total: 0,
    pageSizes: mergedOptions.pageSizes,
    layout: mergedOptions.paginationLayout,
    background: mergedOptions.paginationBackground,
  });

  // 排序和过滤
  const sortParams = ref<TableSortParams | null>(null);
  const filterParams = ref<TableFilterParams>({});

  // 获取数据方法
  const fetchData = async () => {
    loading.value = true;
    error.value = null;
    
    try {
      const params = {
        page: pagination.current,
        pageSize: pagination.pageSize,
        sort: sortParams.value,
        ...filterParams.value,
      };
      
      const { data, total } = await fetchDataFn(params);
      
      tableData.value = data;
      pagination.total = total;
    } catch (err) {
      error.value = err as Error;
      console.error('获取表格数据失败:', err);
    } finally {
      loading.value = false;
    }
  };

  // 页码变化处理器
  const handlePageChange = (page: number) => {
    pagination.current = page;
    fetchData();
  };

  // 每页显示条数变化处理器
  const handleSizeChange = (size: number) => {
    pagination.pageSize = size;
    pagination.current = 1; // 重置到第一页
    fetchData();
  };

  // 排序变化处理器
  const handleSortChange = (sort: TableSortParams) => {
    sortParams.value = sort;
    pagination.current = 1; // 重置到第一页
    fetchData();
  };

  // 过滤器变化处理器
  const handleFilterChange = (filters: TableFilterParams) => {
    filterParams.value = filters;
    pagination.current = 1; // 重置到第一页
    fetchData();
  };

  // 刷新表格数据
  const refreshTable = () => {
    fetchData();
  };

  // 重置表格（包括分页、排序和过滤）
  const resetTable = () => {
    pagination.current = 1;
    pagination.pageSize = mergedOptions.defaultPageSize!;
    sortParams.value = null;
    filterParams.value = {};
    fetchData();
  };

  // 设置过滤参数
  const setFilters = (filters: TableFilterParams) => {
    filterParams.value = { ...filters };
    pagination.current = 1; // 重置到第一页
    fetchData();
  };

  // 自动加载
  if (mergedOptions.autoLoad) {
    fetchData();
  }

  return {
    // 状态
    tableData,
    loading,
    error,
    pagination,
    sortParams,
    filterParams,
    
    // 方法
    fetchData,
    handlePageChange,
    handleSizeChange,
    handleSortChange,
    handleFilterChange,
    refreshTable,
    resetTable,
    setFilters,
  };
} 