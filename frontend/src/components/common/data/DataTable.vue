<template>
  <div class="data-table">
    <!-- 表格工具栏 -->
    <div v-if="$slots.toolbar" class="data-table__toolbar">
      <slot name="toolbar" />
    </div>

    <!-- 表格主体 -->
    <el-table
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
      @cell-mouse-enter="handleCellMouseEnter"
      @cell-mouse-leave="handleCellMouseLeave"
      @cell-click="handleCellClick"
      @cell-dblclick="handleCellDblclick"
      @row-click="handleRowClick"
      @row-dblclick="handleRowDblclick"
      @row-contextmenu="handleRowContextmenu"
      @header-click="handleHeaderClick"
      @header-contextmenu="handleHeaderContextmenu"
      @sort-change="handleSortChange"
      @filter-change="handleFilterChange"
      @current-change="handleCurrentChange"
      @header-dragend="handleHeaderDragend"
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
              {{ column.prop && scope.row[column.prop] }}
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

    <!-- 表格分页 -->
    <div v-if="pagination" class="data-table__pagination">
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
  import type { TableColumnCtx, TableProps } from 'element-plus';

  interface Column {
    prop?: string;
    label?: string;
    type?: string;
    width?: string | number;
    minWidth?: string | number;
    fixed?: boolean | 'left' | 'right';
    sortable?: boolean | 'custom';
    sortMethod?: (a: any, b: any) => number;
    sortBy?: string | string[] | ((row: any) => string);
    formatter?: (row: any, column: TableColumnCtx<any>, cellValue: any, index: number) => string;
    showOverflowTooltip?: boolean;
    align?: 'left' | 'center' | 'right';
    headerAlign?: 'left' | 'center' | 'right';
    className?: string;
    labelClassName?: string;
    header?: boolean;
    filters?: { text: string; value: string }[];
    filterPlacement?: string;
    filterMultiple?: boolean;
    filterMethod?: (value: any, row: any) => boolean;
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
    pageSize?: number;
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
    pagination: false,
    pageSize: 10,
    pageSizes: () => [10, 20, 50, 100],
    paginationLayout: 'total, sizes, prev, pager, next, jumper',
    paginationBackground: true,
    paginationSmall: false,
    hideOnSinglePage: false,
    tableProps: () => ({}),
  });

  const emit = defineEmits<{
    (e: 'select', selection: any[], row: any): void;
    (e: 'select-all', selection: any[]): void;
    (e: 'selection-change', selection: any[]): void;
    (
      e: 'cell-mouse-enter',
      row: any,
      column: TableColumnCtx<any>,
      cell: HTMLElement,
      event: Event,
    ): void;
    (
      e: 'cell-mouse-leave',
      row: any,
      column: TableColumnCtx<any>,
      cell: HTMLElement,
      event: Event,
    ): void;
    (e: 'cell-click', row: any, column: TableColumnCtx<any>, cell: HTMLElement, event: Event): void;
    (
      e: 'cell-dblclick',
      row: any,
      column: TableColumnCtx<any>,
      cell: HTMLElement,
      event: Event,
    ): void;
    (e: 'row-click', row: any, column: TableColumnCtx<any>, event: Event): void;
    (e: 'row-dblclick', row: any, column: TableColumnCtx<any>, event: Event): void;
    (e: 'row-contextmenu', row: any, column: TableColumnCtx<any>, event: Event): void;
    (e: 'header-click', column: TableColumnCtx<any>, event: Event): void;
    (e: 'header-contextmenu', column: TableColumnCtx<any>, event: Event): void;
    (
      e: 'sort-change',
      { column, prop, order }: { column: TableColumnCtx<any>; prop: string; order: string },
    ): void;
    (e: 'filter-change', filters: Record<string, string[]>): void;
    (e: 'current-change', currentRow: any, oldCurrentRow: any): void;
    (
      e: 'header-dragend',
      newWidth: number,
      oldWidth: number,
      column: TableColumnCtx<any>,
      event: Event,
    ): void;
    (e: 'expand-change', row: any, expanded: boolean): void;
    (e: 'size-change', size: number): void;
    (e: 'current-page-change', page: number): void;
  }>();

  // 分页相关
  const currentPage = ref(1);
  const pageSize = ref(props.pageSize);

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

  const handleCellMouseEnter = (
    row: any,
    column: TableColumnCtx<any>,
    cell: HTMLElement,
    event: Event,
  ) => {
    emit('cell-mouse-enter', row, column, cell, event);
  };

  const handleCellMouseLeave = (
    row: any,
    column: TableColumnCtx<any>,
    cell: HTMLElement,
    event: Event,
  ) => {
    emit('cell-mouse-leave', row, column, cell, event);
  };

  const handleCellClick = (
    row: any,
    column: TableColumnCtx<any>,
    cell: HTMLElement,
    event: Event,
  ) => {
    emit('cell-click', row, column, cell, event);
  };

  const handleCellDblclick = (
    row: any,
    column: TableColumnCtx<any>,
    cell: HTMLElement,
    event: Event,
  ) => {
    emit('cell-dblclick', row, column, cell, event);
  };

  const handleRowClick = (row: any, column: TableColumnCtx<any>, event: Event) => {
    emit('row-click', row, column, event);
  };

  const handleRowDblclick = (row: any, column: TableColumnCtx<any>, event: Event) => {
    emit('row-dblclick', row, column, event);
  };

  const handleRowContextmenu = (row: any, column: TableColumnCtx<any>, event: Event) => {
    emit('row-contextmenu', row, column, event);
  };

  const handleHeaderClick = (column: TableColumnCtx<any>, event: Event) => {
    emit('header-click', column, event);
  };

  const handleHeaderContextmenu = (column: TableColumnCtx<any>, event: Event) => {
    emit('header-contextmenu', column, event);
  };

  const handleSortChange = ({
    column,
    prop,
    order,
  }: {
    column: TableColumnCtx<any>;
    prop: string;
    order: string;
  }) => {
    emit('sort-change', { column, prop, order });
  };

  const handleFilterChange = (filters: Record<string, string[]>) => {
    emit('filter-change', filters);
  };

  const handleCurrentChange = (currentRow: any, oldCurrentRow: any) => {
    emit('current-change', currentRow, oldCurrentRow);
  };

  const handleHeaderDragend = (
    newWidth: number,
    oldWidth: number,
    column: TableColumnCtx<any>,
    event: Event,
  ) => {
    emit('header-dragend', newWidth, oldWidth, column, event);
  };

  const handleExpandChange = (row: any, expanded: boolean) => {
    emit('expand-change', row, expanded);
  };

  const handleSizeChange = (size: number) => {
    pageSize.value = size;
    emit('size-change', size);
  };

  const handlePageChange = (page: number) => {
    currentPage.value = page;
    emit('current-page-change', page);
  };
</script>

<style>
  .data-table {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .data-table__toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: var(--spacing-sm);
  }

  .data-table__pagination {
    display: flex;
    justify-content: flex-end;
    margin-top: var(--spacing-md);
  }

  /* 暗色主题 */
  .dark .data-table {
    --el-table-border-color: var(--el-border-color-darker);
    --el-table-header-bg-color: var(--el-bg-color-overlay);
    --el-table-row-hover-bg-color: var(--el-bg-color-overlay);
    --el-table-current-row-bg-color: var(--el-bg-color-overlay);
    --el-table-fixed-box-shadow: var(--el-box-shadow-dark);
    --el-table-header-text-color: var(--el-text-color-primary);
    --el-table-text-color: var(--el-text-color-regular);
  }
</style>
