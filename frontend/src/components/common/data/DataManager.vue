<template>
  <div class="data-manager">
    <!-- 工具栏 -->
    <div v-if="$slots.toolbar" class="data-manager__toolbar">
      <slot name="toolbar" />
    </div>

    <!-- 搜索栏 -->
    <div v-if="$slots.search" class="data-manager__search">
      <slot name="search" />
    </div>

    <!-- 数据表格 -->
    <div class="data-manager__table">
      <el-table
        ref="tableRef"
        v-bind="tableProps"
        :data="data"
        :height="height"
        :max-height="maxHeight"
        :stripe="stripe"
        :border="border"
        :size="size"
        :fit="fit"
        :show-header="showHeader"
        :highlight-current-row="highlightCurrentRow"
        :row-class-name="rowClassName"
        :row-style="rowStyle"
        :cell-class-name="cellClassName"
        :cell-style="cellStyle"
        :header-row-class-name="headerRowClassName"
        :header-row-style="headerRowStyle"
        :header-cell-class-name="headerCellClassName"
        :header-cell-style="headerCellStyle"
        :row-key="rowKey"
        :empty-text="emptyText"
        :default-expand-all="defaultExpandAll"
        :expand-row-keys="expandRowKeys"
        :default-sort="defaultSort"
        :tree-props="treeProps"
        :summary-method="summaryMethod"
        :sum-text="sumText"
        :indent="indent"
        :lazy="lazy"
        :load="load"
        :select-on-indeterminate="selectOnIndeterminate"
        @select="handleSelect"
        @select-all="handleSelectAll"
        @selection-change="handleSelectionChange"
        @cell-mouse-enter="(row, column, cell, event) => handleCellMouseEnter(row, column, cell, event)"
        @cell-mouse-leave="(row, column, cell, event) => handleCellMouseLeave(row, column, cell, event)"
        @cell-click="(row, column, cell, event) => handleCellClick(row, column, cell, event)"
        @cell-dblclick="(row, column, cell, event) => handleCellDblclick(row, column, cell, event)"
        @row-click="(row, column, event) => handleRowClick(row, column, event)"
        @row-dblclick="(row, column, event) => handleRowDblclick(row, column, event)"
        @row-contextmenu="(row, column, event) => handleRowContextmenu(row, column, event)"
        @header-click="(column, event) => handleHeaderClick(column, event)"
        @header-contextmenu="(column, event) => handleHeaderContextmenu(column, event)"
        @sort-change="handleSortChange"
        @filter-change="handleFilterChange"
        @current-change="handleCurrentChange"
        @header-dragend="(newWidth, oldWidth, column, event) => handleHeaderDragend(newWidth, oldWidth, column, event)"
        @expand-change="handleExpandChange"
      >
        <!-- 选择列 -->
        <el-table-column
          v-if="selection"
          type="selection"
          :width="selectionWidth"
          :fixed="selectionFixed"
          :selectable="selectable"
          :reserve-selection="reserveSelection"
        />

        <!-- 索引列 -->
        <el-table-column
          v-if="index"
          type="index"
          :width="indexWidth"
          :fixed="indexFixed"
          :index="indexMethod"
        />

        <!-- 展开列 -->
        <el-table-column v-if="expand" type="expand" :width="expandWidth" :fixed="expandFixed">
          <template #default="scope">
            <slot name="expand" v-bind="scope" />
          </template>
        </el-table-column>

        <!-- 数据列 -->
        <template v-for="column in columns" :key="column.prop || column.type">
          <el-table-column
            v-bind="getColumnProps(column)"
            :align="column.align || align"
            :header-align="column.headerAlign || headerAlign"
          >
            <template v-if="column.header" #header="scope">
              <slot :name="`column-header-${column.prop}`" v-bind="scope">
                {{ scope.column.label }}
              </slot>
            </template>
            <template #default="scope">
              <slot :name="`column-${column.prop}`" v-bind="scope">
                {{ column.prop ? scope.row[column.prop] : '' }}
              </slot>
            </template>
          </el-table-column>
        </template>

        <!-- 操作列 -->
        <el-table-column
          v-if="$slots.action"
          :label="actionLabel"
          :width="actionWidth"
          :fixed="actionFixed"
          :align="actionAlign"
        >
          <template #default="scope">
            <slot name="action" v-bind="scope" />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div v-if="pagination" class="data-manager__pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="pageSizes"
        :layout="paginationLayout"
        :background="paginationBackground"
        :small="paginationSmall"
        :hide-on-single-page="hideOnSinglePage"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed } from 'vue';
  import type { TableColumnCtx, TableInstance, TableProps } from 'element-plus';

  interface Column {
    prop?: string;
    label?: string;
    type?: 'selection' | 'index' | 'expand';
    width?: string | number;
    minWidth?: string | number;
    fixed?: boolean | 'left' | 'right';
    sortable?: boolean;
    sortMethod?: (a: any, b: any) => number;
    sortBy?: string | string[] | ((row: any) => string);
    formatter?: (row: any, column: TableColumnCtx<any>, cellValue: any, index: number) => string;
    showOverflowTooltip?: boolean;
    align?: 'left' | 'center' | 'right';
    headerAlign?: 'left' | 'center' | 'right';
    className?: string;
    labelClassName?: string;
    header?: boolean;
    selectable?: (row: any, index: number) => boolean;
    reserveSelection?: boolean;
    filters?: { text: string; value: string }[];
    filterPlacement?: string;
    filterMultiple?: boolean;
    filterMethod?: (value: string, row: any) => boolean;
    filteredValue?: string[];
  }

  interface Props {
    data: any[];
    columns: Column[];
    height?: string | number;
    maxHeight?: string | number;
    stripe?: boolean;
    border?: boolean;
    size?: 'large' | 'default' | 'small';
    fit?: boolean;
    showHeader?: boolean;
    highlightCurrentRow?: boolean;
    rowClassName?: string | ((params: { row: any; rowIndex: number }) => string);
    rowStyle?: TableProps<any>['rowStyle'];
    cellClassName?: string | ((params: { row: any; column: TableColumnCtx<any>; rowIndex: number; columnIndex: number }) => string);
    cellStyle?: TableProps<any>['cellStyle'];
    headerRowClassName?: string | ((params: { row: any; rowIndex: number }) => string);
    headerRowStyle?: TableProps<any>['headerRowStyle'];
    headerCellClassName?: string | ((params: { row: any; column: TableColumnCtx<any>; rowIndex: number; columnIndex: number }) => string);
    headerCellStyle?: TableProps<any>['headerCellStyle'];
    rowKey?: string | ((row: any) => string);
    emptyText?: string;
    defaultExpandAll?: boolean;
    expandRowKeys?: string[];
    defaultSort?: { prop: string; order: 'ascending' | 'descending' };
    treeProps?: { hasChildren?: string; children?: string };
    summaryMethod?: (params: { columns: TableColumnCtx<any>[]; data: any[] }) => string[];
    sumText?: string;
    indent?: number;
    lazy?: boolean;
    load?: (row: any, treeNode: any, resolve: (data: any[]) => void) => void;
    selectOnIndeterminate?: boolean;
    selection?: boolean;
    selectionWidth?: string | number;
    selectionFixed?: boolean | 'left' | 'right';
    selectable?: (row: any, index: number) => boolean;
    reserveSelection?: boolean;
    index?: boolean;
    indexWidth?: string | number;
    indexFixed?: boolean | 'left' | 'right';
    indexMethod?: (index: number) => number;
    expand?: boolean;
    expandWidth?: string | number;
    expandFixed?: boolean | 'left' | 'right';
    align?: 'left' | 'center' | 'right';
    headerAlign?: 'left' | 'center' | 'right';
    actionLabel?: string;
    actionWidth?: string | number;
    actionFixed?: boolean | 'left' | 'right';
    actionAlign?: 'left' | 'center' | 'right';
    pagination?: boolean;
    total?: number;
    defaultPageSize?: number;
    pageSizes?: number[];
    paginationLayout?: string;
    paginationBackground?: boolean;
    paginationSmall?: boolean;
    hideOnSinglePage?: boolean;
    tableProps?: Record<string, any>;
  }

  const props = withDefaults(defineProps<Props>(), {
    data: () => [],
    columns: () => [],
    stripe: true,
    border: true,
    size: 'default',
    fit: true,
    showHeader: true,
    highlightCurrentRow: false,
    selectOnIndeterminate: true,
    selection: false,
    selectionWidth: 55,
    index: false,
    indexWidth: 55,
    expand: false,
    expandWidth: 50,
    align: 'left',
    headerAlign: 'left',
    actionLabel: '操作',
    actionWidth: 150,
    actionAlign: 'center',
    pagination: true,
    defaultPageSize: 10,
    pageSizes: () => [10, 20, 50, 100],
    paginationLayout: 'total, sizes, prev, pager, next, jumper',
    paginationBackground: true,
    paginationSmall: false,
    hideOnSinglePage: false,
    total: 0,
    tableProps: () => ({}),
  });

  const emit = defineEmits<{
    (e: 'select', selection: any[], row: any): void;
    (e: 'select-all', selection: any[]): void;
    (e: 'selection-change', selection: any[]): void;
    (e: 'cell-mouse-enter', row: any, column: TableColumnCtx<any>, cell: HTMLElement, event: MouseEvent): void;
    (e: 'cell-mouse-leave', row: any, column: TableColumnCtx<any>, cell: HTMLElement, event: MouseEvent): void;
    (e: 'cell-click', row: any, column: TableColumnCtx<any>, cell: HTMLElement, event: MouseEvent): void;
    (e: 'cell-dblclick', row: any, column: TableColumnCtx<any>, cell: HTMLElement, event: MouseEvent): void;
    (e: 'row-click', row: any, column: TableColumnCtx<any>, event: MouseEvent): void;
    (e: 'row-dblclick', row: any, column: TableColumnCtx<any>, event: MouseEvent): void;
    (e: 'row-contextmenu', row: any, column: TableColumnCtx<any>, event: MouseEvent): void;
    (e: 'header-click', column: TableColumnCtx<any>, event: MouseEvent): void;
    (e: 'header-contextmenu', column: TableColumnCtx<any>, event: MouseEvent): void;
    (e: 'sort-change', params: { column: TableColumnCtx<any>; prop: string; order: string }): void;
    (e: 'filter-change', filters: Record<string, string[]>): void;
    (e: 'current-change', currentRow: any, oldCurrentRow: any): void;
    (e: 'header-dragend', newWidth: number, oldWidth: number, column: TableColumnCtx<any>, event: MouseEvent): void;
    (e: 'expand-change', row: any, expanded: boolean): void;
    (e: 'size-change', size: number): void;
    (e: 'page-change', page: number): void;
    (e: 'update:current-page', page: number): void;
    (e: 'update:page-size', size: number): void;
  }>();

  const tableRef = ref<TableInstance>();
  const currentPage = ref(1);
  const pageSize = ref(props.defaultPageSize ?? 10);

  // 获取列属性
  const getColumnProps = (column: Column) => {
    const {
      prop,
      label,
      type,
      width,
      minWidth,
      fixed,
      sortable,
      sortMethod,
      sortBy,
      formatter,
      showOverflowTooltip,
      className,
      labelClassName,
      filters,
      filterPlacement,
      filterMultiple,
      filterMethod,
      filteredValue,
    } = column;

    return {
      prop,
      label,
      type,
      width,
      minWidth,
      fixed,
      sortable,
      sortMethod,
      sortBy,
      formatter,
      showOverflowTooltip,
      className,
      labelClassName,
      filters,
      filterPlacement,
      filterMultiple,
      filterMethod,
      filteredValue,
    };
  };

  // 事件处理
  const handleSelect = (selection: any[], row: any) => {
    emit('select', selection, row);
  };

  const handleSelectAll = (selection: any[]) => {
    emit('select-all', selection);
  };

  const handleSelectionChange = (selection: any[]) => {
    emit('selection-change', selection);
  };

  const handleCellMouseEnter = (row: any, column: TableColumnCtx<any>, cell: HTMLElement, event: Event) => {
    emit('cell-mouse-enter', row, column, cell, event as MouseEvent);
  };

  const handleCellMouseLeave = (row: any, column: TableColumnCtx<any>, cell: HTMLElement, event: Event) => {
    emit('cell-mouse-leave', row, column, cell, event as MouseEvent);
  };

  const handleCellClick = (row: any, column: TableColumnCtx<any>, cell: HTMLElement, event: Event) => {
    emit('cell-click', row, column, cell, event as MouseEvent);
  };

  const handleCellDblclick = (row: any, column: TableColumnCtx<any>, cell: HTMLElement, event: Event) => {
    emit('cell-dblclick', row, column, cell, event as MouseEvent);
  };

  const handleRowClick = (row: any, column: TableColumnCtx<any>, event: Event) => {
    emit('row-click', row, column, event as MouseEvent);
  };

  const handleRowDblclick = (row: any, column: TableColumnCtx<any>, event: Event) => {
    emit('row-dblclick', row, column, event as MouseEvent);
  };

  const handleRowContextmenu = (row: any, column: TableColumnCtx<any>, event: Event) => {
    emit('row-contextmenu', row, column, event as MouseEvent);
  };

  const handleHeaderClick = (column: TableColumnCtx<any>, event: Event) => {
    emit('header-click', column, event as MouseEvent);
  };

  const handleHeaderContextmenu = (column: TableColumnCtx<any>, event: Event) => {
    emit('header-contextmenu', column, event as MouseEvent);
  };

  const handleSortChange = (params: { column: TableColumnCtx<any>; prop: string; order: string }) => {
    emit('sort-change', params);
  };

  const handleFilterChange = (filters: Record<string, string[]>) => {
    emit('filter-change', filters);
  };

  const handleCurrentChange = (currentRow: any, oldCurrentRow: any) => {
    emit('current-change', currentRow, oldCurrentRow);
  };

  const handleHeaderDragend = (newWidth: number, oldWidth: number, column: TableColumnCtx<any>, event: Event) => {
    emit('header-dragend', newWidth, oldWidth, column, event as MouseEvent);
  };

  const handleExpandChange = (row: any, expanded: boolean) => {
    emit('expand-change', row, expanded);
  };

  const handleSizeChange = (size: number) => {
    pageSize.value = size;
    emit('size-change', size);
    emit('update:page-size', size);
  };

  const handlePageChange = (page: number) => {
    currentPage.value = page;
    emit('page-change', page);
    emit('update:current-page', page);
  };

  // 对外暴露方法
  defineExpose({
    clearSelection: () => tableRef.value?.clearSelection(),
    toggleRowSelection: (row: any, selected?: boolean) =>
      tableRef.value?.toggleRowSelection(row, selected),
    toggleAllSelection: () => tableRef.value?.toggleAllSelection(),
    toggleRowExpansion: (row: any, expanded?: boolean) =>
      tableRef.value?.toggleRowExpansion(row, expanded),
    setCurrentRow: (row: any) => tableRef.value?.setCurrentRow(row),
    clearSort: () => tableRef.value?.clearSort(),
    clearFilter: (columnKeys?: string[]) => tableRef.value?.clearFilter(columnKeys),
    doLayout: () => tableRef.value?.doLayout(),
    sort: (prop: string, order: string) => tableRef.value?.sort(prop, order),
  });

  // 表格属性
  const tableProps = computed(() => {
    const { data, columns, ...rest } = props;
    return rest;
  });
</script>

<style>
  .data-manager {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .data-manager__toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: var(--spacing-sm);
  }

  .data-manager__search {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-sm);
  }

  .data-manager__table {
    flex: 1;
  }

  .data-manager__pagination {
    display: flex;
    justify-content: flex-end;
    margin-top: var(--spacing-md);
  }

  /* 暗色主题 */
  .dark .data-manager {
    --el-table-border-color: var(--el-border-color-darker);
    --el-table-header-bg-color: var(--el-bg-color-overlay);
    --el-table-row-hover-bg-color: var(--el-bg-color-overlay);
    --el-table-current-row-bg-color: var(--el-bg-color-overlay);
    --el-table-fixed-box-shadow: var(--el-box-shadow-dark);
    --el-table-header-text-color: var(--el-text-color-primary);
    --el-table-text-color: var(--el-text-color-regular);
  }
</style>
