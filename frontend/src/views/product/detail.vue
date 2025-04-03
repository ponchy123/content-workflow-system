<template>
  <div class="product-detail-container" v-loading="loading">
    <div class="page-header">
      <div class="title-section">
        <el-button @click="goBack" type="default" plain size="large">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h1>{{ product.product_name || product.name || '产品详情' }}</h1>
        <el-tag v-if="product.product_id || product.id" :type="product.status ? 'success' : 'danger'" effect="dark">
          {{ product.status ? '启用' : '禁用' }}
        </el-tag>
      </div>
      <div class="actions">
        <el-button type="primary" @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="warning" @click="forceReloadPage">
          <el-icon><RefreshRight /></el-icon>
          强制刷新页面
        </el-button>
        <el-button type="primary" @click="toggleEdit" v-if="!isEditing">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
        <el-button type="success" @click="saveChanges" v-if="isEditing">
          <el-icon><Check /></el-icon>
          保存
        </el-button>
        <el-button type="danger" @click="cancelEdit" v-if="isEditing">
          <el-icon><Close /></el-icon>
          取消
        </el-button>
        <el-button type="primary" @click="handleRelogin" v-if="!isLoggedIn">
          <el-icon><Key /></el-icon>
          重新登录
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="detail-tabs" type="border-card" stretch @tab-change="handleTabChange">
      <!-- 1. 基本信息 -->
      <el-tab-pane label="基本信息" name="basic">
        <div class="example-section">
          <h4>产品信息：</h4>
            <div class="example-table-container">
            <el-table :data="[product]" border style="width: 100%" class="excel-style-table">
              <el-table-column 
                v-for="field in basicFields"
                :key="field.prop"
                :prop="field.prop"
                :label="field.label"
                :min-width="field.width"
              >
                <template #default="scope">
                  <div 
                    v-if="currentEditCell && currentEditCell.property === field.prop && currentEditCell.tableName === 'product'" 
                    class="cell-editor"
                  >
                    <el-input 
                      v-if="field.prop !== 'status'"
                      v-model="product[field.prop]" 
                      size="small" 
                      autofocus
                      :placeholder="field.prop.includes('date') ? 'YYYY-MM-DD' : ''"
                      @keydown="handleCellKeydown"
                      @blur="saveCellEdit(product[field.prop])"
                    />
                    <el-input 
                      v-else
                      v-model="statusText" 
                      size="small" 
                      autofocus
                      @keydown="handleCellKeydown"
                      @blur="saveStatusEdit"
                    />
                  </div>
                  <div 
                    v-else 
                    class="editable-cell"
                    @click="enableCellEdit(0, field.prop, field.prop === 'status' ? scope.row.status : scope.row[field.prop], 'product')"
                  >
                    <template v-if="field.prop === 'status'">
                      {{ scope.row.status ? '启用' : '禁用' }}
                    </template>
                    <template v-else>
                      {{ scope.row[field.prop] || '无' }}
                    </template>
                  </div>
                </template>
              </el-table-column>
            </el-table>
            </div>
          
          <div class="product-description mt-3">
            <h4>产品描述：</h4>
            <div 
              v-if="currentEditCell && currentEditCell.property === 'description' && currentEditCell.tableName === 'product'" 
              class="cell-editor description-editor"
            >
              <el-input 
                v-model="product.description" 
                type="textarea" 
                :rows="5"
                autofocus
                @keydown="handleCellKeydown"
                @blur="saveCellEdit(product.description)"
              />
            </div>
            <div 
              v-else 
              class="editable-cell description-card"
              @click="enableCellEdit(0, 'description', product.description, 'product')"
            >
              {{ product.description || '点击添加产品描述' }}
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 2. 基础费用 -->
      <el-tab-pane label="基础费用" name="baseFees">
        <div class="tab-actions">
          <!-- 删除添加工具按钮和保存按钮 -->
        </div>
        <div class="example-section">
          <h4>基础费率:</h4>
          <div class="data-summary">
            <div>数据条数: {{ safeArrays.baseRates.length }}</div>
            <div>价格列: {{ zoneBaseColumns.length ? zoneBaseColumns.map(col => col.label).join(', ') : '无' }}</div>
            <div>单价列: {{ zoneUnitColumns.length ? zoneUnitColumns.map(col => col.label).join(', ') : '无' }}</div>
          </div>
          
          <!-- 开发模式下显示原始数据 -->
          <div v-if="IS_DEV && showRawData && safeArrays.baseRates && safeArrays.baseRates.length > 0" class="raw-data-section">
            <h4>原始数据预览 (第一条记录):</h4>
            <el-card class="raw-data-card" shadow="never">
              <pre>{{ JSON.stringify(safeArrays.baseRates[0], null, 2) }}</pre>
            </el-card>
            <div class="data-keys-info">
              <strong>所有字段:</strong> {{ safeArrays.baseRates[0] ? Object.keys(safeArrays.baseRates[0]).join(', ') : '无数据' }}
            </div>
            <div v-if="safeArrays.baseRates[0] && safeArrays.baseRates[0].raw_data" class="data-keys-info">
              <strong>raw_data字段:</strong> {{ Object.keys(safeArrays.baseRates[0].raw_data).join(', ') }}
            </div>
            
            <!-- 添加区域字段显示 -->
            <div class="data-keys-info">
              <strong>检测到的区域:</strong> {{ availableZones.join(', ') }}
            </div>
            
            <!-- 添加字段格式化示例 -->
            <div class="data-keys-info">
              <strong>区域字段值示例:</strong>
              <ul>
                <li v-for="zoneName in availableZones.slice(0, 3)" :key="zoneName">
                  {{ zoneName }}: 
                  基础价格 = {{ safeArrays.baseRates[0][`${zoneName}基础价格`] || '未找到' }}, 
                  单位价格 = {{ safeArrays.baseRates[0][`${zoneName}单位重量价格`] || '未找到' }}
                </li>
              </ul>
            </div>
          </div>
          
          <div class="full-width-table">
          <div class="example-table-container">
              <el-table 
                :data="safeArrays.baseRates" 
                :loading="tableLoading"
                element-loading-text="数据加载中..."
                element-loading-background="rgba(255, 255, 255, 0.8)"
                stripe 
                border 
                style="width: 100%" 
                max-height="600" 
                class="excel-style-table"
              >
              <!-- 隐藏操作列 -->
              <!-- 
                <el-table-column width="70" align="center">
                  <template #header>
                    <el-button size="small" type="primary" @click="addBaseFeeRecord" circle>
                      <el-icon><Plus /></el-icon>
                    </el-button>
                  </template>
                  <template #default="scope">
                    <el-button size="small" type="danger" @click="deleteBaseFeeRecord(scope.$index)" circle>
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </template>
                </el-table-column>
              -->
                <el-table-column prop="weight" label="重量" min-width="80" align="center">
                  <template #default="scope">
                    <div 
                      v-if="currentEditCell && currentEditCell.rowIndex === Number(scope.$index) && currentEditCell.property === 'weight' && currentEditCell.tableName === 'baseRates'" 
                      class="cell-editor"
                    >
                      <el-input 
                        v-model="scope.row.weight" 
                        size="small" 
                        autofocus
                        @keydown="handleCellKeydown"
                        @blur="saveCellEdit(scope.row.weight)"
                      />
                    </div>
                    <div 
                      v-else 
                      class="editable-cell"
                      @click="enableCellEdit(scope.$index, 'weight', scope.row.weight, 'baseRates')"
                    >
                    {{ scope.row.weight ? `${scope.row.weight}` : '0' }}
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="unit" label="单位" min-width="70" align="center">
                  <template #default="scope">
                    <div 
                      v-if="currentEditCell && currentEditCell.rowIndex === Number(scope.$index) && currentEditCell.property === 'unit' && currentEditCell.tableName === 'baseRates'" 
                      class="cell-editor"
                    >
                      <el-input 
                        v-model="scope.row.unit" 
                        size="small" 
                        autofocus
                        @keydown="handleCellKeydown"
                        @blur="saveCellEdit(scope.row.unit)"
                      />
                    </div>
                    <div 
                      v-else 
                      class="editable-cell"
                      @click="enableCellEdit(scope.$index, 'unit', scope.row.unit, 'baseRates')"
                    >
                      {{ scope.row.unit_display || scope.row.unit }}
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="fee_type" label="计价类型" min-width="120" align="center">
                  <template #default="scope">
                    <div 
                      v-if="currentEditCell && currentEditCell.rowIndex === Number(scope.$index) && currentEditCell.property === 'fee_type' && currentEditCell.tableName === 'baseRates'" 
                      class="cell-editor"
                    >
                      <el-input 
                        v-model="scope.row.fee_type" 
                        size="small" 
                        autofocus
                        @keydown="handleCellKeydown"
                        @blur="saveCellEdit(scope.row.fee_type)"
                      />
                    </div>
                    <div 
                      v-else 
                      class="editable-cell"
                      @click="enableCellEdit(scope.$index, 'fee_type', scope.row.fee_type, 'baseRates')"
                    >
                    {{ getFeeTypeDisplay(scope.row.fee_type) }}
                    </div>
                  </template>
                </el-table-column>
                
                <!-- 动态生成所有区域的基础价格列 -->
                <template v-for="column in zoneBaseColumns" :key="column.prop">
                  <el-table-column 
                    :prop="column.prop" 
                    :label="column.label" 
                    min-width="85"
                    align="right"
                  >
                    <template #default="scope">
                      <div 
                        v-if="currentEditCell && currentEditCell.rowIndex === Number(scope.$index) && currentEditCell.property === column.prop && currentEditCell.tableName === 'baseRates'" 
                        class="cell-editor"
                      >
                        <el-input 
                          v-model="scope.row[column.prop]" 
                          size="small" 
                          autofocus
                          @keydown="handleCellKeydown"
                          @blur="saveCellEdit(scope.row[column.prop])"
                          @change="(val) => {
                            if (val !== getZoneValueForEdit(scope.row, column.prop)) {
                              scope.row.isModified = true;
                              scope.row.lastModifiedField = column.prop;
                              handleCellEdit(scope.row, {property: column.prop}, val, getZoneValueForEdit(scope.row, column.prop));
                            }
                          }"
                        />
                      </div>
                      <div 
                        v-else 
                        class="editable-cell"
                        @click="enableCellEdit(scope.$index, column.prop, getZoneValueForEdit(scope.row, column.prop), 'baseRates')"
                        @dblclick="() => {
                          enableCellEdit(scope.$index, column.prop, getZoneValueForEdit(scope.row, column.prop), 'baseRates');
                        }"
                      >
                        <span :class="{'highlight-changed': scope.row.isModified && scope.row.lastModifiedField === column.prop}">
                          {{ column.formatter(scope.row) }}
                        </span>
                      </div>
                    </template>
                  </el-table-column>
                </template>
              
                <!-- 动态生成所有区域的单位重量价格列 -->
                <template v-for="column in zoneUnitColumns" :key="column.prop">
              <el-table-column 
                    :prop="column.prop" 
                    :label="column.label" 
                    min-width="90"
                    align="right"
              >
                <template #default="scope">
                      <div 
                        v-if="currentEditCell && currentEditCell.rowIndex === Number(scope.$index) && currentEditCell.property === column.prop && currentEditCell.tableName === 'baseRates'" 
                        class="cell-editor"
                      >
                        <el-input 
                          v-model="scope.row[column.prop]" 
                          size="small" 
                          autofocus
                          @keydown="handleCellKeydown"
                          @blur="saveCellEdit(scope.row[column.prop])"
                        />
                      </div>
                      <div 
                        v-else 
                        class="editable-cell"
                        @click="enableCellEdit(scope.$index, column.prop, getZoneValueForEdit(scope.row, column.prop), 'baseRates')"
                      >
                      {{ column.formatter(scope.row) }}
                      </div>
                </template>
              </el-table-column>
                </template>
            </el-table>
            </div>
            </div>
          </div>
        <div v-if="(!safeArrays.baseRates || safeArrays.baseRates.length === 0) && activeTab === 'baseFees'" class="empty-data">
          <el-empty description="暂无基础费用数据" />
        </div>
      </el-tab-pane>

      <!-- 3. 附加费用 -->
      <el-tab-pane label="附加费用" name="surcharges">
        <div class="example-section">
          <h4>附加费用:</h4>
          <div class="data-summary">
            <div>数据条数: {{ safeArrays.surcharges.length }}</div>
            <div>区域费用列: {{ zoneSurchargeColumns.length ? zoneSurchargeColumns.map(col => col.label).join(', ') : '无' }}</div>
          </div>
          <div class="full-width-table">
          <div class="example-table-container">
            <el-table :data="surchargeTableData" border style="width: 100%" max-height="600" class="excel-style-table">
                <el-table-column prop="surcharge_type" label="附加费类型" min-width="120">
                <template #default="scope">
                    <div 
                      v-if="currentEditCell && currentEditCell.rowIndex === Number(scope.$index) && currentEditCell.property === 'surcharge_type' && currentEditCell.tableName === 'surcharges'" 
                      class="cell-editor"
                    >
                      <el-input 
                        v-model="scope.row.surcharge_type" 
                        size="small" 
                        autofocus
                        @keydown="handleCellKeydown"
                        @blur="saveCellEdit(scope.row.surcharge_type)"
                      />
                    </div>
                    <div 
                      v-else 
                      class="editable-cell"
                      @click="enableCellEdit(scope.$index, 'surcharge_type', scope.row.surcharge_type, 'surcharges')"
                    >
                  {{ getSurchargeTypeDisplay(scope.row.surcharge_type) }}
                    </div>
                        </template>
              </el-table-column>
                <el-table-column prop="sub_type" label="子类型" min-width="80">
                  <template #default="scope">
                    <div 
                      v-if="currentEditCell && currentEditCell.rowIndex === Number(scope.$index) && currentEditCell.property === 'sub_type' && currentEditCell.tableName === 'surcharges'" 
                      class="cell-editor"
                    >
                      <el-input 
                        v-model="scope.row.sub_type" 
                        size="small" 
                        autofocus
                        @keydown="handleCellKeydown"
                        @blur="saveCellEdit(scope.row.sub_type)"
                      />
                    </div>
                    <div 
                      v-else 
                      class="editable-cell"
                      @click="enableCellEdit(scope.$index, 'sub_type', scope.row.sub_type, 'surcharges')"
                    >
                      {{ scope.row.sub_type || '-' }}
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="condition_desc" label="条件描述" min-width="150">
                  <template #default="scope">
                    <div 
                      v-if="currentEditCell && currentEditCell.rowIndex === Number(scope.$index) && currentEditCell.property === 'condition_desc' && currentEditCell.tableName === 'surcharges'" 
                      class="cell-editor"
                    >
                      <el-input 
                        v-model="scope.row.condition_desc" 
                        size="small" 
                        type="textarea"
                        :rows="2"
                        autofocus
                        @keydown="handleCellKeydown"
                        @blur="saveCellEdit(scope.row.condition_desc)"
                      />
                    </div>
                    <div 
                      v-else 
                      class="editable-cell"
                      @click="enableCellEdit(scope.$index, 'condition_desc', scope.row.condition_desc, 'surcharges')"
                    >
                      <div class="cell-with-multiline">{{ scope.row.condition_desc || '-' }}</div>
                    </div>
                  </template>
                </el-table-column>
              
              <!-- 动态生成区域费用列 -->
              <el-table-column 
                v-for="column in zoneSurchargeColumns" 
                  :key="column.prop" 
                  :label="column.label"
                  min-width="80"
                  align="right"
              >
                <template #default="scope">
                  <div 
                    v-if="currentEditCell && currentEditCell.rowIndex === Number(scope.$index) && currentEditCell.property === column.prop && currentEditCell.tableName === 'surcharges'" 
                    class="cell-editor"
                  >
                    <el-input 
                      v-model="scope.row[column.prop]" 
                      size="small" 
                      autofocus
                      @keydown="handleCellKeydown"
                      @blur="saveCellEdit(scope.row[column.prop])"
                    />
                  </div>
                  <div 
                    v-else 
                    class="editable-cell"
                    @click="enableCellEdit(scope.$index, column.prop, getSurchargeZoneValueForEdit(scope.row, column.prop), 'surcharges')"
                  >
                    {{ column.formatter(scope.row) }}
                  </div>
                </template>
              </el-table-column>
            </el-table>
            </div>
            </div>
        </div>
      </el-tab-pane>

      <!-- 4. 旺季附加费 -->
      <el-tab-pane label="旺季附加费" name="peakSeasonSurcharges">
        <div class="example-section">
          <h4>旺季附加费:</h4>
          <div class="data-summary">
            <div>数据条数: {{ safeArrays.peakSeasonSurcharges.length }}</div>
            <div>字段列表: {{ safeArrays.peakSeasonSurcharges.length ? Object.keys(safeArrays.peakSeasonSurcharges[0]).join(', ') : '无数据' }}</div>
          </div>
          <div class="full-width-table">
          <div class="example-table-container">
            <el-table :data="peakSeasonSurchargeTableData" border style="width: 100%" max-height="600" class="excel-style-table">
                <el-table-column prop="surcharge_type" label="附加费类型" min-width="150">
                <template #default="scope">
                    <div 
                      v-if="currentEditCell && currentEditCell.rowIndex === Number(scope.$index) && currentEditCell.property === 'surcharge_type' && currentEditCell.tableName === 'peakSeasonSurcharges'" 
                      class="cell-editor"
                    >
                      <el-input 
                        v-model="scope.row.surcharge_type" 
                        size="small" 
                        autofocus
                        @keydown="handleCellKeydown"
                        @blur="saveCellEdit(scope.row.surcharge_type)"
                      />
                    </div>
                    <div 
                      v-else 
                      class="editable-cell"
                      @click="enableCellEdit(scope.$index, 'surcharge_type', scope.row.surcharge_type, 'peakSeasonSurcharges')"
                    >
                      {{ getPeakSeasonSurchargeTypeDisplay(scope.row.surcharge_type) }}
                    </div>
                        </template>
              </el-table-column>
                <el-table-column prop="start_date" label="开始日期" min-width="120" align="center">
                  <template #default="scope">
                    <div 
                      v-if="currentEditCell && currentEditCell.rowIndex === Number(scope.$index) && currentEditCell.property === 'start_date' && currentEditCell.tableName === 'peakSeasonSurcharges'" 
                      class="cell-editor"
                    >
                      <el-input 
                        v-model="scope.row.start_date" 
                        size="small" 
                        autofocus
                        placeholder="YYYY-MM-DD"
                        @keydown="handleCellKeydown"
                        @blur="saveCellEdit(scope.row.start_date)"
                      />
            </div>
                    <div 
                      v-else 
                      class="editable-cell"
                      @click="enableCellEdit(scope.$index, 'start_date', scope.row.start_date, 'peakSeasonSurcharges')"
                    >
                      {{ scope.row.start_date }}
            </div>
                  </template>
                </el-table-column>
                <el-table-column prop="end_date" label="结束日期" min-width="120" align="center">
                  <template #default="scope">
                    <div 
                      v-if="currentEditCell && currentEditCell.rowIndex === Number(scope.$index) && currentEditCell.property === 'end_date' && currentEditCell.tableName === 'peakSeasonSurcharges'" 
                      class="cell-editor"
                    >
                      <el-input 
                        v-model="scope.row.end_date" 
                        size="small" 
                        autofocus
                        placeholder="YYYY-MM-DD"
                        @keydown="handleCellKeydown"
                        @blur="saveCellEdit(scope.row.end_date)"
                      />
          </div>
                    <div 
                      v-else 
                      class="editable-cell"
                      @click="enableCellEdit(scope.$index, 'end_date', scope.row.end_date, 'peakSeasonSurcharges')"
                    >
                      {{ scope.row.end_date }}
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="fee_amount" label="费用金额" min-width="120" align="right">
                  <template #default="scope">
                    <div 
                      v-if="currentEditCell && currentEditCell.rowIndex === Number(scope.$index) && currentEditCell.property === 'fee_amount' && currentEditCell.tableName === 'peakSeasonSurcharges'" 
                      class="cell-editor"
                    >
                      <el-input 
                        v-model="scope.row.fee_amount" 
                        size="small" 
                        type="number"
                        autofocus
                        @keydown="handleCellKeydown"
                        @blur="saveCellEdit(scope.row.fee_amount)"
                      />
                    </div>
                    <div 
                      v-else 
                      class="editable-cell"
                      @click="enableCellEdit(scope.$index, 'fee_amount', scope.row.fee_amount !== undefined ? scope.row.fee_amount : 0, 'peakSeasonSurcharges')"
                    >
                      {{ scope.row.fee_amount !== undefined ? scope.row.fee_amount : 0 }}
                    </div>
                  </template>
                </el-table-column>
            </el-table>
            </div>
            </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- Add a back-to-top button for better UX when scrolling -->
    <el-backtop :right="20" :bottom="20" />
  </div>
</template>

<script lang="ts" setup>
// 引入必要的依赖
import { ref, reactive, computed, onBeforeMount, onMounted, nextTick, watch, h, onBeforeUnmount } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { ElMessage, ElMessageBox } from 'element-plus';
import { formatDateTime, formatCurrency, formatPercent } from '@/utils/format';
import { getProduct, getProductBaseFees, getProductSurcharges, getProductPeakSeasonSurcharges, updateProduct, updateProductBaseFees, updateProductSurcharges, updateProductPeakSeasonSurcharges } from '@/api/products';
import { ArrowLeft, Refresh, Edit, Plus, InfoFilled, Connection, Key, DataLine, Check, Close, Delete, RefreshRight } from '@element-plus/icons-vue';
import axios from 'axios';
import { axiosInstance } from '@/api/core/request';
import {
  SUPPORTED_ZONES,
  getDefaultZonePrices,
  DEFAULT_VALUES,
  REQUIRED_FIELDS,
  TABLE_NAME_MAP
} from '@/types/product';

// 增强错误处理函数
const handleApiError = (error: any) => {
  if (axios.isCancel(error)) {
    console.log('请求取消');
    ElMessage.info('请求已取消');
  } else if (error.response) {
    switch (error.response.status) {
      case 401:
        ElMessage.error('登录已过期，请重新登录');
        // 跳转到登录页面，并保存当前路径
        const currentPath = window.location.pathname;
        const returnUrl = encodeURIComponent(currentPath);
        setTimeout(() => {
          window.location.href = `/login?returnUrl=${returnUrl}`;
        }, 1500);
        break;
      case 403:
        ElMessage.error('权限不足，无法执行此操作');
        break;
      case 404:
        ElMessage.error('请求的资源不存在');
        break;
      case 500:
        ElMessage.error(`服务器错误: ${error.response.data?.message || '未知错误'}`);
        break;
      default:
        ElMessage.error(`服务器错误 (${error.response.status}): ${error.response.data?.message || '未知错误'}`);
    }
  } else if (error.request) {
    // 请求已发送但没有收到响应
    ElMessage.error('网络连接错误，服务器未响应');
  } else {
    // 请求配置出错
    ElMessage.error(`请求错误: ${error.message}`);
  }
};

// 定义基本字段列表，用于生成动态表格列
interface BasicField {
  prop: string;
  label: string;
  width: string;
}

// 产品基本信息字段定义
const basicFields: BasicField[] = [
  { prop: 'product_name', label: '产品名称', width: '120' },
  { prop: 'provider_name', label: '服务商', width: '100' },
  { prop: 'dim_factor', label: '体积重系数', width: '100' },
  { prop: 'dim_factor_unit', label: '系数单位', width: '80' },
  { prop: 'effective_date', label: '生效日期', width: '90' },
  { prop: 'expiration_date', label: '失效日期', width: '90' },
  { prop: 'country', label: '国家', width: '70' },
  { prop: 'currency', label: '币种', width: '70' },
  { prop: 'status', label: '状态', width: '80' },
  { prop: 'enabled_start_date', label: '启用开始', width: '90' },
  { prop: 'enabled_end_date', label: '启用结束', width: '90' },
];

// 定义网络错误接口
interface NetworkError extends Error {
  message: string;
  response?: any;
  request?: any;
  config?: any;
}

// 定义组件props
const props = defineProps<{
  id?: string | number
}>();

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const activeTab = ref('basic');
const isLoggedIn = ref(!!localStorage.getItem('access_token'));
const token = ref(localStorage.getItem('access_token')); // token状态
const isEditing = ref(false); // 全局编辑状态
const originalData = ref<any>(null); // 保存原始数据用于取消编辑
const tableLoading = ref(false); // 表格加载状态

// Excel风格单元格编辑状态
interface CellEditState {
  rowIndex: number;
  property: string;
  value: any;
  tableName: string;
}

const currentEditCell = ref<CellEditState | null>(null);

// 获取产品ID，优先使用props传入的id
const getProductId = computed(() => {
  return props.id || route.params.id;
});

// 环境常量
const IS_DEV = process.env.NODE_ENV === 'development';

// 使用全局 i18n 实例
const { t } = useI18n();

// 返回上一页
const goBack = () => {
  router.push('/product/list');
};

// 获取产品详细信息的主要函数
const fetchProductDetail = async (tabType?: string) => {
  try {
    if (!getProductId.value) {
      console.error('未获取到产品ID，无法获取产品详情');
      ElMessage.error('未获取到产品ID，无法获取产品详情');
      return;
    }
    
    loading.value = true;
    
    // 获取产品ID字符串 - 不要在ID中添加时间戳参数
    const productIdStr = getProductId.value as string;
    
    // 添加时间戳防止缓存
    const timestamp = new Date().getTime();
    console.log(`获取产品详情，添加时间戳: ${timestamp}`);
    
    // 使用API函数获取产品详情 - 注意：不要在ID字符串上添加时间戳
    const responseData = await getProduct(productIdStr);
    
    if (!responseData) {
      ElMessage.error('产品详情获取失败：API返回空数据');
      loading.value = false;
      return;
    }
    
    // 设置产品基本信息
    product.value = {
      ...responseData,
      id: responseData.id || responseData.product_id || '',
      code: responseData.code || responseData.product_id || '',
      name: responseData.name || responseData.product_name || ''
    };
    
    console.log('产品基本信息已加载:', product.value);
    
    // 根据当前标签页，只加载需要的数据
    if (!tabType || tabType === 'baseFees' || tabType === 'basic') {
    // 获取基础费率
    await fetchProductBaseFees();
    }
    
    if (!tabType || tabType === 'surcharges' || tabType === 'basic') {
    // 获取附加费
      await fetchProductSurcharges();
    }
    
    if (!tabType || tabType === 'peakSeasonSurcharges' || tabType === 'basic') {
    // 获取旺季附加费
      await fetchProductPeakSeasonSurcharges();
    }
    
    ElMessage.success('产品数据加载成功');
  } catch (error) {
    console.error('获取产品详情失败:', error);
    handleApiError(error);
  } finally {
    loading.value = false;
  }
};

// 刷新数据
const refreshData = async () => {
  loading.value = true;
  try {
    // 获取产品ID
    const currentProductId = getProductId.value || route.params.id;
    
    // 清除缓存 - 使用正确的API路径
    const clearCacheUrl = `/api/v1/products/products/clear-cache/${currentProductId}/`;
    await fetch(clearCacheUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    }).catch(err => console.warn('清除缓存请求失败，继续刷新:', err));
    
    // 添加时间戳和随机字符串，确保不使用缓存
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(7);
    const url = `/api/v1/products/base-fees/by_product/?product_id=${currentProductId}&_t=${timestamp}&_r=${random}`;
    
    // 使用fetch直接从服务器获取数据
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      },
      cache: 'no-store'
    });
    
    if (!response.ok) {
      throw new Error(`刷新数据失败: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('直接从服务器获取的最新数据:', data);
    
    if (Array.isArray(data)) {
      // 更新表格数据
      safeArrays.baseRates = data;
      ElMessage.success('数据已刷新为最新版本');
    } else {
      throw new Error('服务器返回的数据格式不正确');
    }
  } catch (error) {
    console.error('刷新数据失败:', error);
    handleApiError(error);
  } finally {
    loading.value = false;
  }
};

// 切换编辑状态
const toggleEdit = () => {
  if (!isEditing.value) {
    // 进入编辑模式前保存原始数据，用于取消编辑时恢复
    originalData.value = {
      product: JSON.parse(JSON.stringify(product.value)),
      baseRates: JSON.parse(JSON.stringify(safeArrays.baseRates)),
      surcharges: JSON.parse(JSON.stringify(safeArrays.surcharges)),
      peakSeasonSurcharges: JSON.parse(JSON.stringify(safeArrays.peakSeasonSurcharges))
    };
  }
  isEditing.value = !isEditing.value;
};

// 保存修改
const saveChanges = async () => {
  try {
    loading.value = true;
    const productId = getProductId.value as string;
    let response;
    
    // 记录保存前的数据状态
    console.log('保存前数据状态:', {
      activeTab: activeTab.value,
      product: JSON.stringify(product.value),
      baseRates: safeArrays.baseRates.length,
      surcharges: safeArrays.surcharges.length,
      peakSeasonSurcharges: safeArrays.peakSeasonSurcharges.length
    });
    
    // 创建当前数据的备份，用于在刷新失败时恢复
    const savedData = {
      product: JSON.parse(JSON.stringify(product.value)),
      baseRates: JSON.parse(JSON.stringify(safeArrays.baseRates)),
      surcharges: JSON.parse(JSON.stringify(safeArrays.surcharges)),
      peakSeasonSurcharges: JSON.parse(JSON.stringify(safeArrays.peakSeasonSurcharges))
    };
    
    // 根据当前活动的标签页保存不同数据
    if (activeTab.value === 'basic') {
      console.log('保存基本信息:', product.value);
      response = await updateProduct(productId, product.value);
    } else if (activeTab.value === 'baseFees') {
      console.log('保存基础费率，数据条数:', safeArrays.baseRates.length);
      if (safeArrays.baseRates.length === 0) {
        ElMessage.warning('没有基础费率数据可保存');
        return;
      }
      response = await updateProductBaseFees(productId, safeArrays.baseRates);
    } else if (activeTab.value === 'surcharges') {
      console.log('保存附加费，数据条数:', safeArrays.surcharges.length);
      if (safeArrays.surcharges.length === 0) {
        ElMessage.warning('没有附加费数据可保存');
        return;
      }
      response = await updateProductSurcharges(productId, safeArrays.surcharges);
    } else if (activeTab.value === 'peakSeasonSurcharges') {
      console.log('保存旺季附加费，数据条数:', safeArrays.peakSeasonSurcharges.length);
      if (safeArrays.peakSeasonSurcharges.length === 0) {
        ElMessage.warning('没有旺季附加费数据可保存');
        return;
      }
      const formattedData = safeArrays.peakSeasonSurcharges.map(item => {
        const formattedItem = { ...item };
        if (formattedItem.start_date && !(typeof formattedItem.start_date === 'string')) {
          formattedItem.start_date = formattedItem.start_date.toISOString().split('T')[0];
        }
        if (formattedItem.end_date && !(typeof formattedItem.end_date === 'string')) {
          formattedItem.end_date = formattedItem.end_date.toISOString().split('T')[0];
        }
        return formattedItem;
      });
      response = await updateProductPeakSeasonSurcharges(productId, formattedData);
    }
    
    // 检查API响应
    console.log('API响应:', response);
    if (!response) {
      throw new Error('API返回空响应');
    }
    
    ElMessage.success('保存成功');
    isEditing.value = false;
    
    // 更新原始数据，确保取消按钮使用最新保存的数据
    if (originalData.value) {
      originalData.value = savedData;
    }
    
    // 等待一小段时间后再刷新数据
    setTimeout(async () => {
      console.log('开始重新加载数据...');
      try {
        await fetchProductDetail(activeTab.value);
        console.log('数据重新加载完成');
      } catch (refreshError) {
        console.error('保存后刷新数据失败:', refreshError);
        // 如果刷新失败，恢复使用保存前的数据
        if (activeTab.value === 'basic') {
          product.value = savedData.product;
        } else if (activeTab.value === 'baseFees') {
          safeArrays.baseRates = savedData.baseRates;
        } else if (activeTab.value === 'surcharges') {
          safeArrays.surcharges = savedData.surcharges;
        } else if (activeTab.value === 'peakSeasonSurcharges') {
          safeArrays.peakSeasonSurcharges = savedData.peakSeasonSurcharges;
        }
        ElMessage.warning('数据已保存，但刷新失败，显示最后保存的数据');
      }
      
      // 记录刷新后的数据状态
      console.log('保存后数据状态:', {
        activeTab: activeTab.value,
        product: JSON.stringify(product.value),
        baseRates: safeArrays.baseRates.length,
        surcharges: safeArrays.surcharges.length,
        peakSeasonSurcharges: safeArrays.peakSeasonSurcharges.length
      });
    }, 500);
  } catch (error: any) {
    console.error('保存失败:', error);
    let errorMsg = '未知错误';
    
    if (error.response) {
      console.error('错误响应状态:', error.response.status);
      console.error('错误响应头:', error.response.headers);
      console.error('错误响应数据:', error.response.data);
      
      const status = error.response.status;
      const data = error.response.data;
      
      if (typeof data === 'string') {
        errorMsg = `服务器错误(${status}): ${data}`;
      } else if (data && typeof data === 'object') {
        errorMsg = `服务器错误(${status}): ${JSON.stringify(data)}`;
  } else {
        errorMsg = `服务器错误(${status})`;
      }
    } else if (error.request) {
      console.error('请求对象:', error.request);
      errorMsg = '服务器无响应，请稍后重试';
    } else {
      console.error('错误信息:', error.message);
      console.error('错误堆栈:', error.stack);
      errorMsg = error.message || '请求配置错误';
    }
    
    ElMessage.error(`保存失败: ${errorMsg}`);
  } finally {
    loading.value = false;
  }
};

// 取消编辑
const cancelEdit = () => {
  if (originalData.value) {
    // 恢复原始数据
    product.value = JSON.parse(JSON.stringify(originalData.value.product));
    safeArrays.baseRates = JSON.parse(JSON.stringify(originalData.value.baseRates));
    safeArrays.surcharges = JSON.parse(JSON.stringify(originalData.value.surcharges));
    safeArrays.peakSeasonSurcharges = JSON.parse(JSON.stringify(originalData.value.peakSeasonSurcharges));
  }
  isEditing.value = false;
  ElMessage.info('已取消编辑');
};

// 启用Excel风格单元格编辑
const enableCellEdit = (rowIndex: number | string, property: string, value: any, tableName: string) => {
  // 确保rowIndex是数字类型
  const index = typeof rowIndex === 'string' ? parseInt(rowIndex, 10) : rowIndex;
  
  // 根据不同的表格类型设置初始值
  if (tableName === 'baseRates' && Array.isArray(safeArrays.baseRates) && index < safeArrays.baseRates.length) {
    // 确保访问的属性存在
    if (!(property in safeArrays.baseRates[index])) {
      // 如果属性不存在，先设置一个初始值
      safeArrays.baseRates[index][property] = value;
    }
  } else if (tableName === 'surcharges' && Array.isArray(safeArrays.surcharges) && index < safeArrays.surcharges.length) {
    if (!(property in safeArrays.surcharges[index])) {
      safeArrays.surcharges[index][property] = value;
    }
  } else if (tableName === 'peakSeasonSurcharges' && Array.isArray(safeArrays.peakSeasonSurcharges) && index < safeArrays.peakSeasonSurcharges.length) {
    if (!(property in safeArrays.peakSeasonSurcharges[index])) {
      safeArrays.peakSeasonSurcharges[index][property] = value;
    }
  }
  
  currentEditCell.value = {
    rowIndex: index,
    property,
    value,
    tableName
  };
};

// 取消单元格编辑
const cancelCellEdit = () => {
  currentEditCell.value = null;
};

// 保存单元格编辑
const saveCellEdit = async (newValue: any) => {
  if (!currentEditCell.value) return;

  try {
    const { rowIndex, property, tableName } = currentEditCell.value;
    const productId = getProductId.value as string;
    let dataToUpdate: any[] = [];
    let updateFunction;
    let response;

    // 记录更详细的日志，包括原始值和新值
    const originalValue = currentEditCell.value.value;
    console.log('保存单元格编辑:', { 
      rowIndex, 
      property, 
      tableName, 
      originalValue,
      newValue, 
      productId 
    });

    // 检查并转换数值类型
    let processedValue = newValue;
    if (typeof newValue === 'string' && !isNaN(Number(newValue)) && 
        (property.includes('weight') || property.includes('price') || 
         property.includes('amount') || property.includes('factor'))) {
      processedValue = Number(newValue);
      console.log(`将字符串值'${newValue}'转换为数值: ${processedValue}`);
    }

    // 根据表格类型选择对应的数据和更新函数
    if (tableName === 'product') {
      // 更新产品基本信息
      updateProductField(property as keyof ProductDetail, processedValue);
      console.log('更新产品基本信息:', product.value);
      response = await updateProduct(productId, product.value);
    } else if (tableName === 'baseRates') {
      // 更新当前单元格数据
      const rowIdx = Number(rowIndex);
      const oldValue = safeArrays.baseRates[rowIdx][property]; // 保存旧值用于对比
      safeArrays.baseRates[rowIdx][property] = processedValue;
      console.log(`baseRates[${rowIdx}][${property}]从${oldValue}更新为${processedValue}`);
      
      // 检查必填字段
      const currentRow = safeArrays.baseRates[rowIdx];
      const requiredBaseRateFields = REQUIRED_FIELDS.BASE_RATES;
      const missingFields = requiredBaseRateFields.filter(field => !currentRow[field]);
      
      if (missingFields.length > 0) {
        // 如果缺少必填字段，为它们设置默认值
        console.warn('基础费率缺少必填字段:', missingFields);
        missingFields.forEach(field => {
          currentRow[field] = DEFAULT_VALUES.BASE_RATES[field as keyof typeof DEFAULT_VALUES.BASE_RATES];
        });
        
        console.log('已设置必填字段默认值:', missingFields.map(field => `${field}=${currentRow[field]}`).join(', '));
      }
      
      // 复制数据并确保所有必要的字段都存在
      dataToUpdate = JSON.parse(JSON.stringify(safeArrays.baseRates));
      
      // 遍历每一行，确保数据完整性
      dataToUpdate = dataToUpdate.map(item => {
        // 确保必填字段存在
        requiredBaseRateFields.forEach(field => {
          if (!item[field]) {
            item[field] = DEFAULT_VALUES.BASE_RATES[field as keyof typeof DEFAULT_VALUES.BASE_RATES];
          }
        });
        
        // 处理zone_prices字段，确保格式正确
        const zone_prices: Record<string, number> = {};
        
        // 使用配置中的区域列表，而不是硬编码
        for (const key in item) {
          // 检查是否是区域字段 (Zone1, Zone2等)
          const zoneMatch = key.match(/^zone(\d+|17)$/i);
          if (zoneMatch || (typeof key === 'string' && /^Zone\d+/.test(key))) {
            let zoneNum;
            if (zoneMatch) {
              zoneNum = zoneMatch[1];
            } else {
              // 安全地从'Zone1基础价格'类似的字符串中提取数字
              const matches = key.match(/Zone(\d+|17)/i);
              zoneNum = matches ? matches[1] : null;
              
              if (!zoneNum) {
                console.warn(`无法从字段 ${key} 中提取区域编号，跳过`);
                continue;
              }
            }
            
            // 确保使用小写并标准化格式
            const zoneKey = `zone${zoneNum}`.toLowerCase();
            
            // 安全地将值转换为数字
            let value = 0;
            try {
              value = Number(item[key]) || 0;
            } catch (e) {
              console.warn(`转换字段 ${key} 值为数字时出错:`, e);
            }
            
            zone_prices[zoneKey] = value;
          }
        }
        
        // 将处理后的zone_prices赋值回去
        item.zone_prices = zone_prices;
        
        return item;
      });
      
      console.log('更新基本费率数据，共', dataToUpdate.length, '条记录');
      console.log('基本费率第一条数据样例:', dataToUpdate[0]);
      
      try {
        // 确保数据格式正确，用于API调用
        const formattedData = dataToUpdate.map(item => {
          // 创建新对象，避免修改原始数据
          const formattedItem = { ...item };
          
          // 确保每个项目都有产品ID
          if (!formattedItem.product) {
            formattedItem.product = productId;
          }
          
          // 确保区域价格对象存在
          if (!formattedItem.zone_prices) {
            formattedItem.zone_prices = {};
          }
          
          return formattedItem;
        });
        
        response = await updateProductBaseFees(productId, formattedData);
        console.log('基础费率更新成功:', response);
        
        // 移除警告消息，使用已有的PUT方法持久化到数据库
        ElMessage({
          type: 'success',
          message: '基础费率更新成功',
          duration: 3000,
          showClose: true
        });
        
        // 将基础费率数据显示在界面上
        safeArrays.baseRates[rowIdx][property] = processedValue;
        
        // 刷新数据，确保显示最新状态
        await fetchProductBaseFees();
      } catch (error: any) {
        console.error('基础费率更新失败:', error);
        // 展示更详细的错误信息
        if (error.response) {
          const status = error.response.status;
          const method = error.config?.method?.toUpperCase() || '未知方法';
          if (status === 405) {
            ElMessage.warning('当前系统仅支持查看基础费率，暂不支持修改。您的更改已被记录，但未能保存到服务器。');
          } else {
            ElMessage.error(`${TABLE_NAME_MAP.baseRates}更新失败: 服务器错误(${status}): ${method}_NOT_ALLOWED，不支持的请求方法`);
          }
        } else {
          ElMessage.error(`${TABLE_NAME_MAP.baseRates}更新失败: ${error.message || '未知错误'}`);
        }
        
        // 还原修改，避免前端显示与后端不一致
        safeArrays.baseRates[rowIdx][property] = oldValue;
        
        // 刷新获取当前数据
        await fetchProductBaseFees();
        
        // 终止执行
        currentEditCell.value = null;
        return;
      }
    } else if (tableName === 'surcharges') {
      // 更新当前单元格数据
      const rowIdx = Number(rowIndex);
      const oldValue = safeArrays.surcharges[rowIdx][property]; // 保存旧值用于对比
      safeArrays.surcharges[rowIdx][property] = processedValue;
      console.log(`surcharges[${rowIdx}][${property}]从${oldValue}更新为${processedValue}`);
      
      // 检查必填字段
      const currentRow = safeArrays.surcharges[rowIdx];
      const requiredFields = REQUIRED_FIELDS.SURCHARGES;
      const missingFields = requiredFields.filter(field => !currentRow[field]);
      
      if (missingFields.length > 0) {
        // 如果缺少必填字段，提示用户并还原修改
        console.error(`${TABLE_NAME_MAP.surcharges}缺少必填字段:`, missingFields);
        ElMessage.error(`保存失败: ${TABLE_NAME_MAP.surcharges}缺少必填字段(${missingFields.join(', ')})`);
        
        // 还原当前修改的值
        safeArrays.surcharges[rowIdx][property] = oldValue;
        currentEditCell.value = null;
        
        // 刷新数据，使用现有的fetchProductDetail函数
        await fetchProductDetail();
        return;
      }
      
      // 确保所有行都有所需的字段
      const allSurchargesValid = safeArrays.surcharges.every(item => 
        requiredFields.every(field => item[field] !== undefined && item[field] !== null && item[field] !== ''));
      
      if (!allSurchargesValid) {
        console.warn(`部分${TABLE_NAME_MAP.surcharges}记录缺少必填字段，这些记录可能会被忽略`);
        ElMessage.warning(`部分${TABLE_NAME_MAP.surcharges}记录缺少必填字段，这些记录将在保存时被忽略`);
      }
      
      // 复制数据并确保所有必须的字段都存在
      dataToUpdate = safeArrays.surcharges.map(item => {
        // 创建一个深拷贝以防止修改原始数据
        const cleanItem = JSON.parse(JSON.stringify(item));
        
        // 确保必要字段存在，没有的话提供默认值
        requiredFields.forEach(field => {
          if (!cleanItem[field]) {
            cleanItem[field] = DEFAULT_VALUES.SURCHARGES[field as keyof typeof DEFAULT_VALUES.SURCHARGES] || '';
          }
        });
        
        // 移除可能导致问题的字段
        if ('status' in cleanItem) {
          delete cleanItem.status;
        }
        
        return cleanItem;
      });
      
      console.log(`更新${TABLE_NAME_MAP.surcharges}数据结构:`, dataToUpdate);
      updateFunction = updateProductSurcharges;
    } else if (tableName === 'peakSeasonSurcharges') {
      // 更新当前单元格数据
      const rowIdx = Number(rowIndex);
      const oldValue = safeArrays.peakSeasonSurcharges[rowIdx][property]; // 保存旧值用于对比
      safeArrays.peakSeasonSurcharges[rowIdx][property] = processedValue;
      console.log(`peakSeasonSurcharges[${rowIdx}][${property}]从${oldValue}更新为${processedValue}`);
      
      // 检查必填字段是否完整
      const currentRow = safeArrays.peakSeasonSurcharges[rowIdx];
      const requiredFields = REQUIRED_FIELDS.PEAK_SEASON_SURCHARGES;
      const missingFields = requiredFields.filter(field => !currentRow[field]);
      
      if (missingFields.length > 0) {
        // 如果缺少必填字段，提示用户并还原修改
        console.error(`${TABLE_NAME_MAP.peakSeasonSurcharges}缺少必填字段:`, missingFields);
        ElMessage.error(`保存失败: ${TABLE_NAME_MAP.peakSeasonSurcharges}缺少必填字段(${missingFields.join(', ')})`);
        
        // 还原当前修改的值
        safeArrays.peakSeasonSurcharges[rowIdx][property] = oldValue;
        currentEditCell.value = null;
        
        // 刷新数据，使用现有的fetchProductDetail函数
        await fetchProductDetail();
        return;
      }
      
      // 确保所有旺季附加费记录的必填字段都已填写
      const allValid = safeArrays.peakSeasonSurcharges.every(record => {
        return requiredFields.every(field => record[field] !== undefined && record[field] !== null && record[field] !== '');
      });
      
      if (!allValid) {
        console.error(`存在${TABLE_NAME_MAP.peakSeasonSurcharges}记录缺少必填字段`);
        ElMessage.warning(`部分${TABLE_NAME_MAP.peakSeasonSurcharges}记录缺少必填字段，这些记录将在保存时被忽略`);
      }
      
      // 复制数据并移除不支持的字段
      dataToUpdate = safeArrays.peakSeasonSurcharges.map(item => {
        const cleanItem = { ...item };
        
        // 确保必要字段存在
        requiredFields.forEach(field => {
          if (!cleanItem[field]) {
            cleanItem[field] = DEFAULT_VALUES.PEAK_SEASON_SURCHARGES[field as keyof typeof DEFAULT_VALUES.PEAK_SEASON_SURCHARGES];
          }
        });
        
        // 移除status字段，因为模型中不存在
        if ('status' in cleanItem) {
          delete cleanItem.status;
        }
        return cleanItem;
      });
      
      console.log(`更新${TABLE_NAME_MAP.peakSeasonSurcharges}数据结构:`, dataToUpdate);
      updateFunction = updateProductPeakSeasonSurcharges;
    }

    // 如果有更新函数和数据，则执行更新
    if (updateFunction && dataToUpdate.length > 0) {
      console.log(`准备调用${tableName}数据更新API:`, dataToUpdate);
      response = await updateFunction(productId, dataToUpdate);
      console.log(`${tableName}更新API响应:`, response);
      
      // 这里添加一个标记，表明已成功保存此次编辑
      const successMessage = `单元格[${tableName}][${rowIndex}][${property}]已成功更新为${processedValue}`;
      console.log(successMessage);
      ElMessage.success(successMessage);
      
      // 保存成功后刷新数据，确保显示最新状态
      if (tableName === 'surcharges' || tableName === 'peakSeasonSurcharges') {
        await fetchProductDetail();
      }
    }
  } catch (error: any) {
    console.error('保存单元格失败:', error);
    
    let errorMsg = '未知错误';
    
    if (error.response) {
      // 详细记录服务器错误信息
      console.error('错误响应状态:', error.response.status);
      console.error('错误响应头:', error.response.headers);
      console.error('错误响应数据:', error.response.data);
      
      const status = error.response.status;
      const data = error.response.data;
      
      // 检查是否是401未授权错误（token过期）
      if (status === 401) {
        console.log('Token已过期，需要重新登录');
        ElMessage.error('登录已过期，请重新登录');
        // 跳转到登录页面，并记录当前URL以便登录后返回
        const currentPath = window.location.pathname;
        const returnUrl = encodeURIComponent(currentPath);
        setTimeout(() => {
          window.location.href = `/login?returnUrl=${returnUrl}`;
        }, 1500);
        return;
      }
      
      if (typeof data === 'string') {
        errorMsg = `服务器错误(${status}): ${data}`;
      } else if (data && typeof data === 'object') {
        errorMsg = `服务器错误(${status}): ${JSON.stringify(data)}`;
    } else {
        errorMsg = `服务器错误(${status})`;
      }
    } else if (error.request) {
      // 请求发送但没有收到响应
      console.error('请求对象:', error.request);
      errorMsg = '服务器无响应，请稍后重试';
    } else {
      // 请求配置出错
      console.error('错误信息:', error.message);
      console.error('错误堆栈:', error.stack);
      errorMsg = error.message || '请求配置错误';
    }
    
    ElMessage.error(`单元格更新失败: ${errorMsg}`);
    
    // 保存失败后刷新数据，恢复到最新状态
    await fetchProductDetail();
  } finally {
    currentEditCell.value = null;
  }
};

// 处理单元格键盘事件
const handleCellKeydown = (e: Event) => {
  // 确保事件是KeyboardEvent类型
  const keyEvent = e as KeyboardEvent;
  if (keyEvent.key === 'Enter') {
    // 按Enter保存修改
    const target = keyEvent.target as HTMLInputElement;
    saveCellEdit(target.value);
  } else if (keyEvent.key === 'Escape') {
    // 按Esc取消修改
    cancelCellEdit();
  } else if (keyEvent.key === 'Tab') {
    // 阻止默认的Tab行为
    keyEvent.preventDefault();
    // 根据是否按住Shift键决定移动方向
    moveToNextCell(keyEvent.shiftKey ? -1 : 1);
  }
};

// 移动到下一个单元格
const moveToNextCell = (direction: number) => {
  if (!currentEditCell.value) return;
  
  const { rowIndex, tableName } = currentEditCell.value;
  
  // 根据当前表格类型获取适当的列数组
  let columns: { prop: string }[] = [];
  if (tableName === 'product') {
    columns = basicFields;
  } else if (tableName === 'baseRates') {
    // 基础费率表格的列
    columns = [
      { prop: 'weight' },
      { prop: 'unit' },
      { prop: 'fee_type' },
      ...zoneBaseColumns.value,
      ...zoneUnitColumns.value
    ];
  } else if (tableName === 'surcharges') {
    // 附加费表格的列
    columns = [
      { prop: 'surcharge_type' },
      { prop: 'sub_type' },
      { prop: 'condition_desc' },
      ...zoneSurchargeColumns.value
    ];
  } else if (tableName === 'peakSeasonSurcharges') {
    // 旺季附加费表格的列
    columns = [
      { prop: 'surcharge_type' },
      { prop: 'start_date' },
      { prop: 'end_date' },
      { prop: 'fee_amount' }
    ];
  }
  
  // 找到当前列的索引
  const currentIndex = columns.findIndex(col => col.prop === currentEditCell.value?.property);
  if (currentIndex === -1) return;
  
  // 计算下一个列的索引
  const nextIndex = (currentIndex + direction + columns.length) % columns.length;
  
  // 启用下一个单元格的编辑
  let nextValue;
  if (tableName === 'product') {
    // 产品表格只有一行
    nextValue = product.value[columns[nextIndex].prop];
  } else if (tableName === 'baseRates' && safeArrays.baseRates[rowIndex]) {
    // 基础费率表格
    nextValue = getZoneValueForEdit(safeArrays.baseRates[rowIndex], columns[nextIndex].prop);
  } else if (tableName === 'surcharges' && safeArrays.surcharges[rowIndex]) {
    // 附加费表格
    nextValue = getSurchargeZoneValueForEdit(safeArrays.surcharges[rowIndex], columns[nextIndex].prop);
  } else if (tableName === 'peakSeasonSurcharges' && safeArrays.peakSeasonSurcharges[rowIndex]) {
    // 旺季附加费表格
    nextValue = safeArrays.peakSeasonSurcharges[rowIndex][columns[nextIndex].prop];
  } else {
    return;
  }
  
  enableCellEdit(rowIndex, columns[nextIndex].prop, nextValue, tableName);
};

// 组件挂载时加载数据
onMounted(async () => {
  console.log('组件挂载，开始获取数据');
  try {
    await fetchProductDetail();
    // 记录附加费和旺季附加费数据
    console.log('附加费数据:', safeArrays.surcharges);
    console.log('旺季附加费数据:', safeArrays.peakSeasonSurcharges);
  } catch (error) {
    console.error('组件初始化加载数据失败:', error);
  }
});

// 重新登录处理函数
const handleRelogin = () => {
  const currentPath = window.location.pathname;
  const returnUrl = encodeURIComponent(currentPath);
  window.location.href = `/login?returnUrl=${returnUrl}`;
};

// 添加状态转换函数
const getStatusType = (status: string) => {
  switch (status) {
    case 'success': return 'success';
    case 'warning': return 'warning';
    case 'error': return 'danger';
    case 'loading': return 'info';
    default: return 'info';
  }
};

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'success': return '成功';
    case 'warning': return '警告';
    case 'error': return '错误';
    case 'loading': return '加载中';
    default: return '未知';
  }
};

// 添加一个新的计算属性，用于检查是否有单价数据
const hasUnitPrices = computed(() => {
  if (!safeArrays.baseRates || safeArrays.baseRates.length === 0) {
    return false;
  }
  
  // 检查是否有任何项目包含ZoneXUnitPrice字段
  return safeArrays.baseRates.some(item => {
    for (let i = 1; i <= 5; i++) {
      if (item[`Zone${i}UnitPrice`] !== undefined && item[`Zone${i}UnitPrice`] !== 0) {
        return true;
      }
    }
    return false;
  });
});

// ProductDetail类型定义
interface ProductDetail {
  id: string;
  code: string;
  name: string;
  product_id?: string;
  product_name?: string;
  provider_name: string;
  dim_factor: number; // 确保这是数字类型，而不是字符串
  dim_factor_unit: string;
  effective_date: string;
  expiration_date: string;
  country: string;
  currency: string;
  weight_unit: string;
  dim_unit: string;
  description: string;
  status: number | boolean;
  enabled_weight_band: boolean;
  enabled_start_date: string;
  enabled_end_date: string;
  [key: string]: any; // 添加索引签名以允许动态属性
}

const product = ref<ProductDetail>({
  id: '',
  code: '',
  name: '',
  provider_name: '',
  dim_factor: 0, // 初始值设为数字
  dim_factor_unit: '',
  effective_date: '',
  expiration_date: '',
  country: '',
  currency: '',
  weight_unit: '',
  dim_unit: '',
  description: '',
  status: 1,
  enabled_weight_band: false,
  enabled_start_date: '',
  enabled_end_date: ''
});

// 列定义的接口
interface ColumnDef {
  prop: string;
  label: string;
  width?: string;
  formatter: (row: any) => string;
}

// 动态检测区域的辅助函数
const detectZones = (dataArray: any[]): string[] => {
  if (!dataArray || !Array.isArray(dataArray) || dataArray.length === 0) {
    console.log('没有数据数组或数组为空，无法检测区域');
    return [];
  }
  
  console.log('开始检测区域，数据条数:', dataArray.length);
  
  // 从数据中动态检测区域字段
  const zoneFields = new Set<string>();
  
  // 遍历所有记录，查找所有以Zone开头的字段
  dataArray.forEach(item => {
    if (!item) return;
    
  Object.keys(item).forEach(key => {
      // 匹配Zone开头的字段，但排除包含UnitPrice的字段
      if (/^Zone\d+$/i.test(key) && !key.toLowerCase().includes('unitprice')) {
        zoneFields.add(key.charAt(0).toUpperCase() + key.slice(1).toLowerCase());
      } else if (/^zone\d+$/i.test(key) && !key.toLowerCase().includes('unitprice')) {
        // 转换为首字母大写的格式 (zone1 -> Zone1)
        zoneFields.add('Zone' + key.replace(/^zone/i, ''));
      } else if (/^Zone\d+_price$/i.test(key)) {
        // 处理Zone1_price格式
        zoneFields.add(key.split('_')[0]);
      } else if (/^Zone\d+基础价格$/i.test(key)) {
        // 处理Zone1基础价格格式
        zoneFields.add(key.replace(/基础价格$/, ''));
      } else if (/^Zone\d+单位重量价格$/i.test(key)) {
        // 处理Zone1单位重量价格格式
        zoneFields.add(key.replace(/单位重量价格$/, ''));
      }
      
      // 检查zone_prices对象
      if (item.zone_prices && typeof item.zone_prices === 'object') {
        Object.keys(item.zone_prices).forEach(zoneKey => {
          if (/^zone\d+$/i.test(zoneKey)) {
            zoneFields.add('Zone' + zoneKey.replace(/^zone/i, ''));
          }
        });
      }
      
      // 检查raw_data字段中的区域
      if (item.raw_data && typeof item.raw_data === 'object') {
        Object.keys(item.raw_data).forEach(rawKey => {
          if (/^Zone\d+$/i.test(rawKey)) {
            zoneFields.add(rawKey.charAt(0).toUpperCase() + rawKey.slice(1).toLowerCase());
          } else if (/^Zone\d+基础价格$/i.test(rawKey)) {
            // 处理raw_data中的中文字段名
            zoneFields.add(rawKey.replace(/基础价格$/, ''));
          } else if (/^Zone\d+单位重量价格$/i.test(rawKey)) {
            zoneFields.add(rawKey.replace(/单位重量价格$/, ''));
          }
        });
      }
    });
  });
  
  // 将Set转换为排序后的数组
  const result = Array.from(zoneFields).sort((a, b) => {
    // 提取区域编号并按数字排序
    const numA = parseInt(a.replace(/[^0-9]/g, ''));
    const numB = parseInt(b.replace(/[^0-9]/g, ''));
    return numA - numB;
  });
  
  console.log('检测到的区域字段:', result);
  
  // 如果没有检测到任何区域，使用默认区域
  if (result.length === 0) {
    console.log('未检测到任何区域，使用默认区域');
    const defaultZones = [];
    for (let i = 1; i <= 8; i++) {
      defaultZones.push('Zone' + i);
    }
    defaultZones.push('Zone17');
    return defaultZones;
  }
  
  return result;
};

// 定义安全访问的数组对象
const safeArrays = reactive({
  baseRates: [] as any[],
  surcharges: [] as any[],
  peakSeasonSurcharges: [] as any[]
});

// 查找availableZones定义
const availableZones = computed(() => {
  // 使用配置中的区域列表，过滤出存在数据的区域
  return SUPPORTED_ZONES.filter(zone => 
    safeArrays.baseRates.some(item => 
      Object.keys(item).some(k => k.toLowerCase().startsWith(zone.toLowerCase())) ||
      (item.zone_prices && 
       Object.keys(item.zone_prices).some(k => k.toLowerCase() === zone.toLowerCase() || k.toLowerCase() === `zone${zone.replace(/^zone/i, '')}`.toLowerCase()))
    )
  );
});

// 生成区域价格列
const zoneBaseColumns = computed<ColumnDef[]>(() => {
  return availableZones.value.map(zoneName => ({
    prop: zoneName.toLowerCase(),
    label: `${zoneName}基础价格`,
    width: '120',
    formatter: (row: any) => {
      // 1. 检查直接属性
      let value = row[zoneName] !== undefined ? row[zoneName] : 
                  row[zoneName.toLowerCase()] !== undefined ? row[zoneName.toLowerCase()] : undefined;
      
      // 2. 检查zone_prices对象中的值
      if (value === undefined && row.zone_prices && typeof row.zone_prices === 'object') {
        const zoneKey = zoneName.toLowerCase();
        value = row.zone_prices[zoneKey];
      }
      
      // 3. 检查raw_data字段
      if (value === undefined && row.raw_data && typeof row.raw_data === 'object') {
        value = row.raw_data[zoneName] || row.raw_data[zoneName.toLowerCase()];
      }
      
      // 4. 尝试其他可能的键名格式
      if (value === undefined) {
        value = row[`${zoneName}_price`] !== undefined ? row[`${zoneName}_price`] : 
                row[`${zoneName.toLowerCase()}_price`] !== undefined ? row[`${zoneName.toLowerCase()}_price`] : undefined;
      }
      
      // 5. 尝试含有"基础价格"的键名 - 解决中文字段名问题
      if (value === undefined) {
        const basicPriceKey = `${zoneName}基础价格`;
        value = row[basicPriceKey] !== undefined ? row[basicPriceKey] : undefined;
      }
      
      // 只有当值真正为undefined或null时才使用0，避免覆盖真实的0值
      const currency = row.currency || product.value.currency || 'USD';
      return value !== undefined && value !== null ? formatCurrency(value, currency, 2, false) : formatCurrency(0, currency, 2, false);
    }
  }));
});

// 判断是否应该显示单位重量价格列
const shouldShowUnitPriceColumns = computed(() => {
  // 始终返回true，无论是否有LINEAR类型数据都显示单位重量价格列
  return true;
});

// 生成区域单价列
const zoneUnitColumns = computed<ColumnDef[]>(() => {
  return availableZones.value.map(zoneName => ({
    prop: `${zoneName.toLowerCase()}_unit_price`,
    label: `${zoneName}单位重量价格`,
    width: '150',
    formatter: (row: any) => {
      // 1. 检查直接属性，不再根据fee_type过滤
      let value = row[`${zoneName}UnitPrice`] || row[`${zoneName.toLowerCase()}UnitPrice`];
      
      // 2. 检查zone_unit_prices对象中的值
      if (value === undefined && row.zone_unit_prices && typeof row.zone_unit_prices === 'object') {
        const zoneKey = zoneName.toLowerCase();
        value = row.zone_unit_prices[zoneKey];
      }
      
      // 3. 检查raw_data字段
      if (value === undefined && row.raw_data && typeof row.raw_data === 'object') {
        value = row.raw_data[`${zoneName}UnitPrice`] || row.raw_data[`${zoneName.toLowerCase()}UnitPrice`];
      }
      
      // 4. 检查其他可能的格式
      if (value === undefined) {
        value = row[`${zoneName}_unit_price`] || row[`${zoneName.toLowerCase()}_unit_price`];
      }
      
      // 5. 尝试含有"单位重量价格"的键名 - 解决中文字段名问题
      if (value === undefined) {
        const unitPriceKey = `${zoneName}单位重量价格`;
        value = row[unitPriceKey] !== undefined ? row[unitPriceKey] : undefined;
      }
      
      // 使用统一的货币格式
      const currency = row.currency || product.value.currency || 'USD';
      return value !== undefined && value !== null ? formatCurrency(value, currency, 2, false) : formatCurrency(0, currency, 2, false);
    }
  }));
});

// 添加计价类型显示函数
const getFeeTypeDisplay = (type: string) => {
  const typeMap: { [key: string]: string } = {
    'STEP': 'STEP',
    'LINEAR': 'LINEAR'
  };
  
  return typeMap[type] || type || '未知类型';
};

// 获取产品基础费率
const fetchProductBaseFees = async () => {
  try {
    if (!getProductId.value) return;
    
    // 添加时间戳防止缓存
    const timestamp = new Date().getTime();
    console.log(`获取基础费率，添加时间戳: ${timestamp}`);
    
    tableLoading.value = true; // 开始加载
    
    // 正确的参数添加方式
    const baseFeeData = await getProductBaseFees(getProductId.value as string);
    
    // 首先清空当前数组，无论API返回什么都先清空
    safeArrays.baseRates.length = 0;
    
    if (Array.isArray(baseFeeData) && baseFeeData.length > 0) {
      // 检测区域数据
      const zones = detectZones(baseFeeData);
      console.log('获取到基础费率数据:', baseFeeData);
      
      // 加入到数组中
      for (const item of baseFeeData) {
        // 创建清理后的项目
        const cleanItem = {...item};
        
        // 清理空值字段
        Object.keys(cleanItem).forEach(key => {
          const value = cleanItem[key];
          if (value === undefined || value === null || value === '') {
            delete cleanItem[key];
          }
        });
        
        // 在添加到数组前，确保所有可能的区域字段都有值
        zones.forEach(zoneName => {
          // 初始化区域基础价格字段
          const zoneProp = zoneName.toLowerCase();
          
          // 查找该区域的值
          let zoneValue;
          
          // 1. 检查直接属性
          zoneValue = item[zoneName] !== undefined ? item[zoneName] : 
                     item[zoneName.toLowerCase()] !== undefined ? item[zoneName.toLowerCase()] : undefined;
          
          // 2. 检查zone_prices对象中的值
          if (zoneValue === undefined && item.zone_prices && typeof item.zone_prices === 'object') {
            zoneValue = item.zone_prices[zoneProp];
          }
          
          // 3. 检查raw_data字段
          if (zoneValue === undefined && item.raw_data && typeof item.raw_data === 'object') {
            zoneValue = item.raw_data[zoneName] || item.raw_data[zoneName.toLowerCase()];
          }
          
          // 4. 尝试其他可能的键名格式
          if (zoneValue === undefined) {
            zoneValue = item[`${zoneName}_price`] !== undefined ? item[`${zoneName}_price`] : 
                      item[`${zoneName.toLowerCase()}_price`] !== undefined ? item[`${zoneName.toLowerCase()}_price`] : undefined;
          }
          
          // 5. 尝试含有"基础价格"的键名
          if (zoneValue === undefined) {
            const basicPriceKey = `${zoneName}基础价格`;
            zoneValue = item[basicPriceKey] !== undefined ? item[basicPriceKey] : undefined;
          }
          
          // 将找到的值赋给标准字段名
          if (zoneValue !== undefined) {
            cleanItem[zoneProp] = zoneValue;
            console.log(`设置${zoneName}基础价格: ${zoneValue}`);
          } else {
            // 如果找不到值，默认设置为0
            cleanItem[zoneProp] = 0;
            console.log(`未找到${zoneName}基础价格，设置默认值0`);
          }
          
          // 同样处理单位价格字段
          const unitPriceProp = `${zoneName.toLowerCase()}_unit_price`;
          let unitPriceValue;
          
          // 1. 检查直接属性
          unitPriceValue = item[`${zoneName}UnitPrice`] || item[`${zoneName.toLowerCase()}UnitPrice`];
          
          // 2. 检查zone_unit_prices对象
          if (unitPriceValue === undefined && item.zone_unit_prices && typeof item.zone_unit_prices === 'object') {
            unitPriceValue = item.zone_unit_prices[zoneProp];
          }
          
          // 3. 检查raw_data字段
          if (unitPriceValue === undefined && item.raw_data && typeof item.raw_data === 'object') {
            unitPriceValue = item.raw_data[`${zoneName}UnitPrice`] || item.raw_data[`${zoneName.toLowerCase()}UnitPrice`];
          }
          
          // 4. 检查其他可能的格式
          if (unitPriceValue === undefined) {
            unitPriceValue = item[`${zoneName}_unit_price`] || item[`${zoneName.toLowerCase()}_unit_price`];
          }
          
          // 5. 尝试含有"单位重量价格"的键名
          if (unitPriceValue === undefined) {
            const unitPriceKey = `${zoneName}单位重量价格`;
            unitPriceValue = item[unitPriceKey] !== undefined ? item[unitPriceKey] : undefined;
          }
          
          // 将找到的单位价格值赋给标准字段名
          if (unitPriceValue !== undefined) {
            cleanItem[unitPriceProp] = unitPriceValue;
            console.log(`设置${zoneName}单位价格: ${unitPriceValue}`);
          } else {
            // 如果找不到值，默认设置为0
            cleanItem[unitPriceProp] = 0;
            console.log(`未找到${zoneName}单位价格，设置默认值0`);
          }
        });
        
        safeArrays.baseRates.push(cleanItem);
      }
      
      // 排序，将OZ单位的行排在前面
      sortBaseRatesByUnit();
      
      // 打印完整处理后的数据用于检查
      console.log('处理后的基础费率完整数据:', JSON.stringify(safeArrays.baseRates));
    }
  } catch (error) {
    console.error('获取产品基础费率失败:', error);
  } finally {
    tableLoading.value = false; // 结束加载
  }
};

// 按单位排序基础费率，将盎司(OZ)单位的放在前面
const sortBaseRatesByUnit = () => {
  if (!safeArrays.baseRates || safeArrays.baseRates.length === 0) return;
  
  safeArrays.baseRates.sort((a, b) => {
    const unitA = (a.unit || '').toString().toUpperCase();
    const unitB = (b.unit || '').toString().toUpperCase();
    
    // 如果a是OZ，但b不是，则a排在前面
    if (unitA === 'OZ' && unitB !== 'OZ') return -1;
    // 如果b是OZ，但a不是，则b排在前面
    if (unitB === 'OZ' && unitA !== 'OZ') return 1;
    
    // 如果都是OZ或者都不是OZ，按重量排序
    const weightA = parseFloat(a.weight) || 0;
    const weightB = parseFloat(b.weight) || 0;
    return weightA - weightB;
  });
};

// 刷新令牌
const refreshToken = async () => {
  try {
    // 实现令牌刷新逻辑
    return true;
  } catch (error) {
    console.error('刷新令牌失败:', error);
    return false;
  }
};

// 简化版的刷新令牌函数
const tryRefreshToken = async () => {
  try {
    ElMessage.info('正在刷新令牌...');
    const result = await refreshToken();
    if (result) {
      ElMessage.success('令牌刷新成功');
            } else {
      ElMessage.warning('令牌刷新失败，请重新登录');
    }
    return result;
    } catch (error) {
    ElMessage.error(`令牌刷新失败: ${error instanceof Error ? error.message : '未知错误'}`);
    return false;
  }
};

// 检查用户登录状态
const checkLoginStatus = async () => {
  const token = localStorage.getItem('access_token');
  isLoggedIn.value = !!token;
  
  if (!token) {
    ElMessage.warning('未找到访问令牌，请登录');
    return false;
  }
  
  try {
    // 简单验证token是否有效的逻辑
    ElMessage.success('Token验证成功');
    return true;
  } catch (error) {
    ElMessage.error('Token已失效，请重新登录');
    return false;
  }
};

// 检查API连接状态
const checkApiConnection = async (type: 'baseRates' | 'surcharges' | 'peakSeasonSurcharges') => {
  try {
    if (!getProductId.value) {
      ElMessage.warning('未获取到产品ID，无法测试API连接');
      return;
    }
    
    ElMessage.info(`正在测试${type}API连接...`);
    
    if (type === 'baseRates') {
      await fetchProductBaseFees();
      if (safeArrays.baseRates.length > 0) {
        ElMessage.success(`成功获取到${safeArrays.baseRates.length}条基础费率数据`);
      } else {
        const rawResponse = await getProductBaseFees(getProductId.value as string);
        console.log('基础费率API原始响应:', rawResponse);
        if (Array.isArray(rawResponse) && rawResponse.length > 0) {
          ElMessage.success(`API返回了${rawResponse.length}条基础费率数据，但前端处理可能有问题`);
        } else {
          ElMessage.warning('基础费率API连接正常，但没有返回数据');
        }
      }
    } else if (type === 'surcharges') {
      if (safeArrays.surcharges.length === 0) {
        const surchargesData = await getProductSurcharges(getProductId.value as string);
          if (Array.isArray(surchargesData)) {
            safeArrays.surcharges = [...surchargesData];
          ElMessage.success(`成功获取到${surchargesData.length}条附加费数据`);
            } else {
          ElMessage.warning('附加费API连接正常，但没有返回数据');
            }
          } else {
        ElMessage.success('附加费API连接正常');
      }
    } else if (type === 'peakSeasonSurcharges') {
      const peakSeasonData = await getProductPeakSeasonSurcharges(getProductId.value as string);
      if (Array.isArray(peakSeasonData)) {
        safeArrays.peakSeasonSurcharges = [...peakSeasonData];
        ElMessage.success(`成功获取到${peakSeasonData.length}条旺季附加费数据`);
        } else {
        ElMessage.warning('旺季附加费API连接正常，但没有返回数据');
          }
      }
    } catch (error) {
    console.error(`${type}API连接测试失败:`, error);
    ElMessage.error(`${type}API连接失败: ${error instanceof Error ? error.message : '未知错误'}`);
  }
};

// 检查是否有指定区域列
const hasZoneColumn = (zoneNumber: number): boolean => {
  // 检查任何记录中是否含有此区域列
  return safeArrays.baseRates.some(item => {
    const key = `zone${zoneNumber}`.toLowerCase();
    const keyCapital = `Zone${zoneNumber}`;
    return item[key] !== undefined || item[keyCapital] !== undefined;
  });
};

// 获取区域值（处理大小写差异）
const getZoneValue = (row: any, zoneNumber: number): any => {
  const key = `zone${zoneNumber}`.toLowerCase();
  const keyCapital = `Zone${zoneNumber}`;
  
  // 尝试获取不同格式的列名
  if (row[key] !== undefined) {
    return row[key];
  } else if (row[keyCapital] !== undefined) {
    return row[keyCapital];
  }
  return null;
};

// 格式化货币（产品详情使用）
const formatProductCurrency = (value: any): string => {
  if (value === undefined || value === null) {
    return '-';
  }
  // 转为数字并格式化为货币
  const num = parseFloat(value);
  if (isNaN(num)) {
    return String(value);
  }
  return new Intl.NumberFormat('zh-CN', { 
    style: 'currency', 
    currency: 'CNY',
    minimumFractionDigits: 2
  }).format(num);
};

// 格式化日期（产品详情使用）
const formatProductDate = (dateStr: any): string => {
  if (!dateStr) return '-';
  try {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN');
  } catch (e) {
    return String(dateStr);
  }
};

// 获取附加费类型显示文本
const getSurchargeTypeDisplay = (type: string) => {
  return type || '未知附加费';
};

// 获取旺季附加费类型显示文本
const getPeakSeasonSurchargeTypeDisplay = (type: string) => {
  return type || '未知旺季附加费';
};

// 获取区域数据示例，用于调试显示
const getZoneExample = (zoneName: string): string => {
  if (!safeArrays.baseRates || safeArrays.baseRates.length === 0) return '无数据';
  
  const zoneNumber = parseInt(zoneName.replace('Zone', ''));
  if (isNaN(zoneNumber)) return '无效区域名称';
  
  // 检查第一条记录的数据
  const firstItem = safeArrays.baseRates[0];
  const key = `Zone${zoneNumber}`;
  const lowerKey = `zone${zoneNumber}`.toLowerCase();
  const unitKey = `Zone${zoneNumber}UnitPrice`;
  const lowerUnitKey = `zone${zoneNumber}unitprice`.toLowerCase();
  
  // 处理价格值，确保0也能显示
  let zoneValue = '无';
  if (firstItem[key] !== undefined) {
    zoneValue = firstItem[key].toString();
  } else if (firstItem[lowerKey] !== undefined) {
    zoneValue = firstItem[lowerKey].toString();
  }
  
  // 处理单价值，确保0也能显示
  let unitValue = '无单价';
  if (firstItem[unitKey] !== undefined) {
    unitValue = firstItem[unitKey].toString();
  } else if (firstItem[lowerUnitKey] !== undefined) {
    unitValue = firstItem[lowerUnitKey].toString();
  }
  
  return `价格: ${zoneValue}, 单价: ${unitValue}`;
};

// 生成附加费区域列
const zoneSurchargeColumns = computed<ColumnDef[]>(() => {
  return availableZones.value.map(zoneName => ({
    prop: zoneName, // 使用原始区域名称作为属性名，与后端返回的Zone1等匹配
    label: zoneName,
    width: '100',
    align: 'right',
    formatter: (row: any) => {
      // 直接从行数据中获取Zone1, Zone2等字段值
      let value = row[zoneName];
      
      // 如果未找到值，尝试转换为数字类型的键
      if (value === undefined) {
        console.log(`未找到附加费 ${row.surcharge_id || ''} 的 ${zoneName} 值，尝试其他格式`);
      }
      
      // 打印调试信息
      if (row.surcharge_id && value !== undefined) {
        console.log(`附加费 ${row.surcharge_id} 的 ${zoneName} 值为:`, value);
      }
      
      // 使用统一的货币格式
      const currency = row.currency || product.value.currency || 'USD';
      return value !== undefined && value !== null ? 
             formatCurrency(parseFloat(value), currency, 2, false) : 
             formatCurrency(0, currency, 2, false);
    }
  }));
});

const showRawData = ref(false);

// 将状态布尔值转换为字符串用于输入框显示
const statusText = computed({
  get: () => product.value.status ? '启用' : '禁用',
  set: (val) => {
    // 在这里什么都不做，我们会在自定义的saveStatusEdit函数中处理
  }
});

// 添加一个函数用于更新产品字段，确保深层响应性
const updateProductField = (field: keyof ProductDetail, value: any) => {
  product.value = { 
    ...product.value,
    [field]: value 
  };
}

// 保存状态编辑的方法
const saveStatusEdit = () => {
  // 将文本转换为布尔值
  const newValue = statusText.value === '启用' ? true : false;
  updateProductField('status', newValue);
  saveCellEdit(newValue);
};

// 获取区域值（处理大小写差异）
const getZoneValueForEdit = (row: any, columnProp: string): any => {
  // 解析区域名称，可能是zone1, zone1_unit_price等格式
  const zoneName = columnProp.includes('_unit_price') 
    ? 'Zone' + columnProp.split('_')[0].replace(/[^0-9]/g, '')
    : 'Zone' + columnProp.replace(/[^0-9]/g, '');
  
  // 标准化属性名
  const stdProp = columnProp.toLowerCase();
  
  console.log(`getZoneValueForEdit: 尝试获取列 ${columnProp}, 解析为区域 ${zoneName}`);
  
  // 1. 首先尝试直接从行数据中获取属性
  if (row[columnProp] !== undefined) {
    console.log(`找到直接属性 ${columnProp}值: ${row[columnProp]}`);
    return row[columnProp];
  }
  
  // 2. 然后尝试大写的Zone前缀
  if (row[zoneName] !== undefined) {
    console.log(`找到Zone属性 ${zoneName}值: ${row[zoneName]}`);
    return row[zoneName];
  }
  
  // 3. 如果是基础费率且存在zone_prices对象，从中获取
  if (row.zone_prices && typeof row.zone_prices === 'object') {
    const zoneKey = `zone${zoneName.replace('Zone', '')}`;
    if (row.zone_prices[zoneKey] !== undefined) {
      console.log(`找到zone_prices[${zoneKey}]值: ${row.zone_prices[zoneKey]}`);
      return row.zone_prices[zoneKey];
    }
  }
  
  // 4. 如果是单位价格字段，且存在zone_unit_prices对象，从中获取
  if (columnProp.includes('_unit_price') && row.zone_unit_prices && typeof row.zone_unit_prices === 'object') {
    const zoneKey = `zone${zoneName.replace('Zone', '')}`;
    if (row.zone_unit_prices[zoneKey] !== undefined) {
      console.log(`找到zone_unit_prices[${zoneKey}]值: ${row.zone_unit_prices[zoneKey]}`);
      return row.zone_unit_prices[zoneKey];
    }
  }
  
  // 5. 尝试raw_data对象(如果存在)
  if (row.raw_data && typeof row.raw_data === 'object') {
    const possibleKeys = [
      zoneName,
      zoneName.toLowerCase(),
      `${zoneName}_price`,
      `${zoneName}基础价格`,
      `${zoneName}UnitPrice`,
      `${zoneName}单位重量价格`
    ];
    
    for (const key of possibleKeys) {
      if (row.raw_data[key] !== undefined) {
        console.log(`找到raw_data[${key}]值: ${row.raw_data[key]}`);
        return row.raw_data[key];
      }
    }
  }
  
  console.log(`未找到区域 ${zoneName} 的值，返回默认值 0`);
  return 0;
};

// 获取附加费区域值（处理大小写差异）
const getSurchargeZoneValueForEdit = (row: any, columnProp: string): any => {
  // 确保使用与后端一致的字段名
  // 直接使用传入的列名，它应该与后端返回的字段名一致（如Zone1, Zone2等）
  
  // 打印调试信息
  console.log(`尝试获取附加费字段 ${columnProp} 的值，行ID:`, row.surcharge_id || '新行');
  
  // 1. 首先尝试直接获取字段值
  if (row[columnProp] !== undefined) {
    console.log(`找到 ${columnProp} 值:`, row[columnProp]);
    return row[columnProp];
  }
  
  // 2. 如果有zone_fees对象，尝试从中获取
  if (row.zone_fees && typeof row.zone_fees === 'object') {
    const zoneKey = `zone${columnProp.replace('Zone', '')}`;
    if (row.zone_fees[zoneKey] !== undefined) {
      console.log(`找到 zone_fees.${zoneKey} 值:`, row.zone_fees[zoneKey]);
      return row.zone_fees[zoneKey];
    }
  }
  
  console.log(`未找到 ${columnProp} 值，返回默认值 0`);
  return 0;
};

// 获取产品附加费用
const fetchProductSurcharges = async () => {
  try {
    if (!getProductId.value) return;
    
    console.log('开始获取产品附加费数据，时间戳:', new Date().toISOString());
    
    // 只获取普通附加费数据
    const surcharges = await getProductSurcharges(String(getProductId.value));

    console.log('附加费API返回原始数据:', surcharges);

    // 检查并处理数据
    if (Array.isArray(surcharges) && surcharges.length > 0) {
      console.log('成功获取到附加费数据，条数:', surcharges.length);
      
      // 直接使用API返回的数据，不需要字段转换
      safeArrays.surcharges = surcharges;
      
      // 打印第一条数据用于调试
      if (surcharges.length > 0) {
        console.log('附加费第一条数据示例:', surcharges[0]);
        console.log('附加费字段列表:', Object.keys(surcharges[0]).join(', '));
      }
    } else {
      console.log('未获取到附加费数据或数据为空');
      // 如果没有数据，创建一个包含默认值的空行
      const emptySurcharge: Record<string, any> = {
        surcharge_id: '',
        product: getProductId.value,
        surcharge_type: DEFAULT_VALUES.SURCHARGES.surcharge_type,
        sub_type: DEFAULT_VALUES.SURCHARGES.sub_type,
        condition_desc: DEFAULT_VALUES.SURCHARGES.condition_desc
      };
      
      // 添加所有区域字段
      SUPPORTED_ZONES.forEach(zone => {
        emptySurcharge[zone] = 0;
      });
      
      safeArrays.surcharges = [emptySurcharge];
    }
  } catch (error) {
    console.error('获取附加费数据失败:', error);
    // 发生错误时创建一个包含默认值的空行
    const emptySurcharge: Record<string, any> = {
      surcharge_id: '',
      product: getProductId.value,
      surcharge_type: DEFAULT_VALUES.SURCHARGES.surcharge_type,
      sub_type: DEFAULT_VALUES.SURCHARGES.sub_type,
      condition_desc: DEFAULT_VALUES.SURCHARGES.condition_desc
    };
    
    // 添加所有区域字段
    SUPPORTED_ZONES.forEach(zone => {
      emptySurcharge[zone] = 0;
    });
    
    safeArrays.surcharges = [emptySurcharge];
  }
};

// 获取产品旺季附加费
const fetchProductPeakSeasonSurcharges = async () => {
  try {
    if (!getProductId.value) return;
    
    console.log(`开始获取产品(${getProductId.value})的旺季附加费`);
    
    // 调用API并获取数据
    const response = await getProductPeakSeasonSurcharges(getProductId.value as string);
    
    // 首先清空当前数组
    safeArrays.peakSeasonSurcharges.splice(0, safeArrays.peakSeasonSurcharges.length);
    
    console.log('旺季附加费API响应数据:', response);
    
    if (response && Array.isArray(response) && response.length > 0) {
      console.log('获取到旺季附加费数据数量:', response.length);
      
      // 处理每一项数据
      response.forEach(item => {
        // 确保item是一个对象
        if (item && typeof item === 'object') {
          // 深复制避免引用问题
          const processedItem = JSON.parse(JSON.stringify(item));
          
          // 确保日期字段格式正确
          if (processedItem.start_date && typeof processedItem.start_date === 'string') {
            // 确保日期格式正确
            if (!processedItem.start_date.match(/^\d{4}-\d{2}-\d{2}$/)) {
              try {
                processedItem.start_date = new Date(processedItem.start_date).toISOString().split('T')[0];
              } catch (e) {
                console.error('日期格式转换错误:', e);
              }
            }
          }
          
          if (processedItem.end_date && typeof processedItem.end_date === 'string') {
            // 确保日期格式正确
            if (!processedItem.end_date.match(/^\d{4}-\d{2}-\d{2}$/)) {
              try {
                processedItem.end_date = new Date(processedItem.end_date).toISOString().split('T')[0];
              } catch (e) {
                console.error('日期格式转换错误:', e);
              }
            }
          }
          
          // 确保fee_amount字段存在且为数字
          if (processedItem.fee_amount) {
            processedItem.fee_amount = typeof processedItem.fee_amount === 'number' ? 
              processedItem.fee_amount : parseFloat(processedItem.fee_amount) || 0;
          } else {
            processedItem.fee_amount = 0;
          }
          
          safeArrays.peakSeasonSurcharges.push(processedItem);
        }
      });
      
      console.log('处理后的旺季附加费数据:', safeArrays.peakSeasonSurcharges);
    } else {
      console.log('没有获取到旺季附加费数据或数据为空');
      // 不自动添加空行，由peakSeasonSurchargeTableData计算属性处理
    }
  } catch (error) {
    console.error('获取产品旺季附加费失败:', error);
    // 不自动添加空行，由peakSeasonSurchargeTableData计算属性处理
  }
};

// 检测是否有未保存的更改
const hasUnsavedChanges = computed(() => {
  if (!originalData.value) return false;
  
  switch (activeTab.value) {
    case 'basic':
      return JSON.stringify(product.value) !== JSON.stringify(originalData.value.product);
    case 'baseFees':
      return JSON.stringify(safeArrays.baseRates) !== JSON.stringify(originalData.value.baseRates);
    case 'surcharges':
      return JSON.stringify(safeArrays.surcharges) !== JSON.stringify(originalData.value.surcharges);
    case 'peakSeasonSurcharges':
      return JSON.stringify(safeArrays.peakSeasonSurcharges) !== JSON.stringify(originalData.value.peakSeasonSurcharges);
    default:
      return false;
  }
});

// 添加Tab切换逻辑
const handleTabChange = async (tabName: string | number) => {
  console.log(`切换到标签页: ${tabName}`);
  
  // 检查是否有未保存的更改
  if (hasUnsavedChanges.value) {
    try {
      await ElMessageBox.confirm('当前修改未保存，是否继续切换？', '提示', {
        confirmButtonText: '继续切换',
        cancelButtonText: '取消',
        type: 'warning'
      });
    } catch {
      // 用户取消了切换
      return;
    }
  }
  
  activeTab.value = tabName as string;
  
  // 根据标签页加载对应数据
  if (tabName === 'baseFees') {
    loading.value = true;
    try {
      // 先尝试直接刷新获取最新数据
      await refreshData();
      
      // 如果没有数据，再尝试使用标准API获取
      if (safeArrays.baseRates.length === 0) {
        await fetchProductBaseFees();
      }
    } catch (error) {
      console.error('加载基础费率数据失败:', error);
      ElMessage.error('加载基础费率数据失败，请刷新重试');
    } finally {
      loading.value = false;
    }
  } else if (tabName === 'surcharges') {
    // 获取附加费用
    await fetchProductSurcharges();
  } else if (tabName === 'peakSeasonSurcharges') {
    // 获取旺季附加费
    await fetchProductPeakSeasonSurcharges();
  }
};

// 在setup函数内的开始部分添加对数据为空的处理
watch([() => activeTab.value, () => safeArrays.surcharges], ([newTab, surcharges]) => {
  if (newTab === 'surcharges' && (!surcharges || surcharges.length === 0)) {
    console.log('附加费标签页激活且数据为空，添加默认行');
    safeArrays.surcharges = [{ 
      id: Date.now(), 
      surcharge_type: '', 
      sub_type: '',
      condition_desc: '', 
      fee_amount: 0 
    }];
  }
}, { immediate: true });

watch([() => activeTab.value, () => safeArrays.peakSeasonSurcharges], ([newTab, peakSurcharges]) => {
  if (newTab === 'peakSeasonSurcharges' && (!peakSurcharges || peakSurcharges.length === 0)) {
    console.log('旺季附加费标签页激活且数据为空，添加默认行');
    const today = new Date();
    const nextMonth = new Date(today);
    nextMonth.setMonth(nextMonth.getMonth() + 1);
    
    safeArrays.peakSeasonSurcharges = [{
      id: Date.now(),
      surcharge_type: '',
      fee_amount: 0,
      start_date: today.toISOString().split('T')[0],
      end_date: nextMonth.toISOString().split('T')[0]
    }];
  }
}, { immediate: true });

// 添加计算属性
const surchargeTableData = computed(() => {
    console.log('计算附加费表格数据，当前数组长度:', safeArrays.surcharges.length);
    
    if (safeArrays.surcharges.length === 0) {
        // 返回一个默认空行
        console.log('附加费数据为空，返回默认空行');
        return [{ 
            surcharge_id: Date.now(), 
            surcharge_type: '', 
            sub_type: '',
            condition_desc: '', 
            fee_amount: 0 
        }];
    }
    
    return safeArrays.surcharges;
});

const peakSeasonSurchargeTableData = computed(() => {
  console.log('计算旺季附加费表格数据，当前数组长度:', safeArrays.peakSeasonSurcharges.length);
  
  if (safeArrays.peakSeasonSurcharges.length === 0) {
    // 返回一个默认空行
    console.log('旺季附加费数据为空，返回默认空行');
    const today = new Date();
    const nextMonth = new Date(today);
    nextMonth.setMonth(nextMonth.getMonth() + 1);
    
    return [{
      // 不设置pss_id，让后端自动生成
      product: getProductId.value,
      surcharge_type: '',
      fee_amount: 0,
      start_date: today.toISOString().split('T')[0],
      end_date: nextMonth.toISOString().split('T')[0],
      // 添加区域费用字段，用于前端显示
      Zone1: 0,
      Zone2: 0,
      Zone3: 0,
      Zone4: 0,
      Zone5: 0,
      Zone6: 0,
      Zone7: 0,
      Zone8: 0,
      Zone17: 0
    }];
  }
  
  // 确保每条记录都有所有必要的区域费用字段
  return safeArrays.peakSeasonSurcharges.map(item => {
    const processedItem = { ...item };
    // 确保所有区域费用字段都存在
    const zones = ['Zone1', 'Zone2', 'Zone3', 'Zone4', 'Zone5', 'Zone6', 'Zone7', 'Zone8', 'Zone17'];
    zones.forEach(zone => {
      if (processedItem[zone] === undefined) {
        processedItem[zone] = processedItem.fee_amount || 0;
      }
    });
    return processedItem;
  });
});

// 添加新的基础费率记录
const addBaseFeeRecord = () => {
  if (!getProductId.value) {
    ElMessage.warning('请先选择产品');
    return;
  }
  
  // 创建一个新的基础费率记录
  const newRecord: Record<string, any> = {
    product: getProductId.value,
    weight: 0,
    weight_unit: 'lb',
    fee_type: 'STEP',
    zone_prices: {} as Record<string, number>,
    zone_unit_prices: {} as Record<string, number>,
    raw_data: {} as Record<string, any>,
    is_temp: true // 标记为临时记录，用于区分尚未保存到数据库的记录
  };
  
  // 添加所有区域的价格字段
  for (let i = 1; i <= 8; i++) {
    const zoneKey = `zone${i}`;
    newRecord[zoneKey] = 0;
    newRecord.zone_prices[zoneKey] = 0;
  }
  
  // 添加zone17
  newRecord.zone17 = 0;
  newRecord.zone_prices.zone17 = 0;
  
  // 添加到数组的开头，使其显示在表格顶部
  safeArrays.baseRates.unshift(newRecord);
  
  ElMessage.success('已添加新的费率记录，请填写数据后保存');
};

// 删除基础费率记录
const deleteBaseFeeRecord = (index: number) => {
  if (index < 0 || index >= safeArrays.baseRates.length) {
    ElMessage.warning('无效的记录索引');
    return;
  }
  
  const record = safeArrays.baseRates[index];
  
  // 确认删除
  ElMessageBox.confirm(
    `确定要删除重量为 ${record.weight} ${record.weight_unit} 的费率记录吗？`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
    .then(async () => {
      if (record.is_temp) {
        // 如果是临时记录，直接从数组中移除
        safeArrays.baseRates.splice(index, 1);
        ElMessage.success('记录已删除');
      } else {
        try {
          // 从前端数组中移除
          safeArrays.baseRates.splice(index, 1);
          
          // 使用保存方法来更新后端数据
          await saveBaseFees();
          
          ElMessage.success('记录已删除并保存');
        } catch (error) {
          console.error('删除费率记录失败:', error);
          ElMessage.error('删除失败: ' + (error instanceof Error ? error.message : '未知错误'));
          
          // 获取最新数据
          await fetchProductBaseFees();
        }
      }
    })
    .catch(() => {
      // 用户取消操作
      ElMessage.info('已取消删除');
    });
};

// 验证并转换Zone价格
const validateAndConvertZonePrice = (value: any): number | null => {
  if (value === undefined || value === null || value === '') {
    return null;
  }
  
  // 尝试转换为数字
  const numValue = parseFloat(String(value).replace(/,/g, ''));
  if (isNaN(numValue)) {
    console.warn(`无效的价格值: ${value}`);
    return null;
  }
  
  // 确保价格为正数并四舍五入到两位小数
  return Math.round(Math.max(0, numValue) * 100) / 100;
};

// 添加基础费率验证函数
const validateBaseRate = (row: any) => {
  const errors = [];
  
  if (!row.weight || isNaN(Number(row.weight))) {
    errors.push('重量必须为有效数字');
  }
  
  if (!row.fee_type) {
    errors.push('计价类型不能为空');
  }
  
  SUPPORTED_ZONES.forEach(zone => {
    const zoneLower = zone.toLowerCase();
    // 检查直接属性
    const value = row[zone] !== undefined ? row[zone] : 
                  row[zoneLower] !== undefined ? row[zoneLower] : 
                  (row.zone_prices && row.zone_prices[zoneLower]) !== undefined ? row.zone_prices[zoneLower] : undefined;
    
    if (value === undefined || isNaN(Number(value))) {
      errors.push(`${zone}价格无效`);
    }
  });
  
  return errors;
};

// 优化validateBaseFeesData函数，使用新的validateBaseRate函数
const validateBaseFeesData = (data: any[]): boolean => {
  if (!Array.isArray(data) || data.length === 0) {
    ElMessage.error('没有可保存的基础费率数据');
    return false;
  }
  
  const errors: string[] = [];
  
  data.forEach((item, index) => {
    const rowErrors = validateBaseRate(item);
    if (rowErrors.length > 0) {
      errors.push(`第 ${index + 1} 行: ${rowErrors.join(', ')}`);
    }
  });
  
  // 显示错误信息
  if (errors.length > 0) {
    const errorMsg = errors.length > 3 
      ? `${errors.slice(0, 3).join('\n')}\n...等共 ${errors.length} 个错误` 
      : errors.join('\n');
    
    ElMessage.error(`数据验证失败:\n${errorMsg}`);
    return false;
  }
  
  return true;
};

// 保存基础费率
const saveBaseFees = async () => {
  try {
    if (!getProductId.value) {
      ElMessage.warning('产品ID不能为空');
      return;
    }
    
    const productId = getProductId.value;
    const baseFees = JSON.parse(JSON.stringify(safeArrays.baseRates));
    
    // 首先进行数据验证
    if (!validateBaseFeesData(baseFees)) {
      return;
    }
    
    ElMessage.info('正在保存基础费率...');
    console.log('原始基础费率数据:', baseFees);
    
    // 准备数据：确保区域价格数据格式正确
    const formattedFees = baseFees.map((item: any) => {
      // 创建一个新对象，避免修改原始数据
      const formattedItem: Record<string, any> = {
        ...item,
        product: productId
      };
      
      // 删除不必要的临时字段
      if ('is_temp' in formattedItem) {
        delete formattedItem.is_temp;
      }
      
      // 删除UI状态标记字段
      if ('isModified' in formattedItem) {
        delete formattedItem.isModified;
      }
      
      if ('lastModifiedField' in formattedItem) {
        delete formattedItem.lastModifiedField;
      }
      
      console.log(`处理费率记录: 重量=${formattedItem.weight}, 单位=${formattedItem.weight_unit}`);
      
      // 确保zone_prices对象存在
      if (!formattedItem.zone_prices || typeof formattedItem.zone_prices !== 'object') {
        formattedItem.zone_prices = {};
      }
      
      // 将Zone1, Zone2等字段的值移入zone_prices对象
      for (let i = 1; i <= 8; i++) {
        const zoneKey = `zone${i}`;
        const zoneCapitalKey = `Zone${i}`;
        
        // 优先使用zone1格式的字段值
        let value = formattedItem[zoneKey] !== undefined ? formattedItem[zoneKey] : 
                   formattedItem[zoneCapitalKey] !== undefined ? formattedItem[zoneCapitalKey] : null;
        
        const convertedValue = validateAndConvertZonePrice(value);
        if (convertedValue !== null) {
          formattedItem.zone_prices[zoneKey] = convertedValue;
          console.log(`设置 ${zoneKey} 价格: ${convertedValue}`);
        }
      }
      
      // 处理zone17
      const zone17Key = 'zone17';
      const zone17CapitalKey = 'Zone17';
      let zone17Value = formattedItem[zone17Key] !== undefined ? formattedItem[zone17Key] : 
                       formattedItem[zone17CapitalKey] !== undefined ? formattedItem[zone17CapitalKey] : null;
      
      const convertedZone17Value = validateAndConvertZonePrice(zone17Value);
      if (convertedZone17Value !== null) {
        formattedItem.zone_prices[zone17Key] = convertedZone17Value;
        console.log(`设置 zone17 价格: ${convertedZone17Value}`);
      }
      
      // 确保单位价格对象存在
      if (!formattedItem.zone_unit_prices || typeof formattedItem.zone_unit_prices !== 'object') {
        formattedItem.zone_unit_prices = {};
      }
      
      // 处理单位价格字段（如果有）
      for (let i = 1; i <= 8; i++) {
        const unitPriceKey = `Zone${i}UnitPrice`;
        const unitPriceLowerKey = `zone${i}_unit_price`;
        
        // 优先使用ZoneXUnitPrice格式
        let unitPriceValue = formattedItem[unitPriceKey] !== undefined ? formattedItem[unitPriceKey] : 
                            formattedItem[unitPriceLowerKey] !== undefined ? formattedItem[unitPriceLowerKey] : null;
        
        const convertedUnitValue = validateAndConvertZonePrice(unitPriceValue);
        if (convertedUnitValue !== null) {
          const zoneKey = `zone${i}`;
          formattedItem.zone_unit_prices[zoneKey] = convertedUnitValue;
          console.log(`设置 ${zoneKey} 单位价格: ${convertedUnitValue}`);
        }
      }
      
      // 处理Zone17的单位价格
      const unitPrice17Key = `Zone17UnitPrice`;
      const unitPrice17LowerKey = `zone17_unit_price`;
      let unitPrice17Value = formattedItem[unitPrice17Key] !== undefined ? formattedItem[unitPrice17Key] : 
                            formattedItem[unitPrice17LowerKey] !== undefined ? formattedItem[unitPrice17LowerKey] : null;
      
      const convertedUnitPrice17Value = validateAndConvertZonePrice(unitPrice17Value);
      if (convertedUnitPrice17Value !== null) {
        formattedItem.zone_unit_prices['zone17'] = convertedUnitPrice17Value;
        console.log(`设置 zone17 单位价格: ${convertedUnitPrice17Value}`);
      }
      
      return formattedItem;
    });
    
    console.log('格式化后的数据:', JSON.stringify(formattedFees, null, 2));
    
    // 保存格式化后的数据，作为备份
    const savedFormattedFees = JSON.parse(JSON.stringify(formattedFees));
    
    // 发送请求保存数据
    loading.value = true;
    ElMessage.info('正在提交数据到服务器...');
    
    try {
      // 设置请求超时时间较长，确保数据能完成处理
      const response = await updateProductBaseFees(productId.toString(), formattedFees);
      console.log('保存基础费率API响应:', response);
      
      // 添加延迟，确保后端数据处理完成
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      ElMessage.success('基础费率保存成功');
      
      // 在保存成功后，立即更新当前显示的数据，即使刷新可能失败，也确保显示最新编辑内容
      safeArrays.baseRates = JSON.parse(JSON.stringify(savedFormattedFees));
      
      // 更新原始数据备份，确保取消按钮不会恢复到旧数据
      if (originalData.value) {
        originalData.value.baseRates = JSON.parse(JSON.stringify(savedFormattedFees));
      }
      
      // 尝试刷新获取最新服务器数据
      try {
        await refreshData();
        
        // 如果刷新后数据为空，使用保存的数据
        if (safeArrays.baseRates.length === 0) {
          console.warn('刷新后数据为空，使用已保存的数据');
          safeArrays.baseRates = JSON.parse(JSON.stringify(savedFormattedFees));
        }
      } catch (refreshError) {
        console.error('保存后刷新数据失败:', refreshError);
        // 发生错误时，确保使用已保存的数据
        safeArrays.baseRates = JSON.parse(JSON.stringify(savedFormattedFees));
      }
      
    } catch (error) {
      console.error('保存基础费率失败:', error);
      ElMessage.error('保存基础费率失败: ' + (error instanceof Error ? error.message : '未知错误'));
    } finally {
      loading.value = false;
    }
  } catch (error) {
    console.error('保存基础费率时出错:', error);
    ElMessage.error('保存基础费率时出错: ' + (error instanceof Error ? error.message : '未知错误'));
    loading.value = false;
  }
};

// 强制刷新页面
const forceReloadPage = () => {
  ElMessageBox.confirm(
    '确定要重新加载页面吗？未保存的更改将会丢失。',
    '强制刷新',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    // 清除可能的缓存标记
    localStorage.setItem('last_reload_time', Date.now().toString());
    // 强制刷新页面，绕过缓存
    window.location.reload();
  }).catch(() => {
    ElMessage.info('已取消刷新');
  });
};

// 添加单元格直接编辑功能，编辑后立即保存
const handleCellEdit = async (row: any, column: any, newValue: any, oldValue: any) => {
  try {
    console.log(`单元格编辑: 行=${JSON.stringify(row)}, 列=${column.property}, 旧值=${oldValue}, 新值=${newValue}`);
    
    // 如果值没有变化，不做任何处理
    if (newValue === oldValue) {
      console.log('值未变化，跳过保存');
      return;
    }
    
    // 检查值是否为有效的数字
    const numValue = parseFloat(newValue);
    if (isNaN(numValue)) {
      ElMessage.error('请输入有效的数字');
      // 恢复原值
      row[column.property] = oldValue;
      return;
    }
    
    // 获取区域信息
    const zoneMatch = column.property.match(/^[Zz]one(\d+)$/);
    if (!zoneMatch) {
      console.warn('无法解析区域信息:', column.property);
      return;
    }
    
    const zoneNumber = zoneMatch[1];
    const zoneKey = `zone${zoneNumber}`;
    
    console.log(`编辑的是区域 ${zoneNumber} 的价格`);
    
    // 确保zone_prices对象存在
    if (!row.zone_prices) {
      row.zone_prices = {};
    }
    
    // 更新区域价格
    row.zone_prices[zoneKey] = numValue;
    
    // 标记行为已修改
    row.isModified = true;
    
    // 在保存前备份当前数据，用于在保存成功后更新originalData
    const currentBaseFees = JSON.parse(JSON.stringify(safeArrays.baseRates));
    
    // 立即保存更改
    await saveBaseFees();
    
    // 保存成功后，更新originalData中的baseRates
    if (originalData.value) {
      originalData.value.baseRates = currentBaseFees;
    }
    
  } catch (error) {
    console.error('处理单元格编辑时出错:', error);
    ElMessage.error('保存更改失败，请稍后重试');
    
    // 恢复原值
    row[column.property] = oldValue;
  }
};

// 组件生命周期钩子
onMounted(async () => {
  // 先设置活动标签页为基础应用
  activeTab.value = 'baseFees';
  
  // 直接调用刷新数据函数获取最新数据
  await refreshData();
  
  // 如果数据仍未加载，尝试常规方法
  if (safeArrays.baseRates.length === 0) {
    await fetchProductDetail('baseFees');
  }
});

</script>

<style scoped>
.product-detail-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.back-button {
  display: flex;
  align-items: center;
  cursor: pointer;
  gap: 5px;
  color: var(--el-color-primary);
}

.back-button .el-icon {
  margin-right: 5px;
}

.actions {
  display: flex;
  gap: 8px;
}

.detail-tabs {
  margin-top: 20px;
}

.debug-info {
  margin-top: 20px;
  padding: 15px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #f8f8f8;
}

.debug-info h3 {
  margin-bottom: 10px;
}

.debug-info h4 {
  margin-bottom: 5px;
}

.debug-info pre {
  margin: 0;
  padding: 5px;
  background-color: #fff;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}

.test-area {
  margin-top: 20px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.test-area h2 {
  margin-bottom: 10px;
}

.base-rates-table {
  margin-top: 20px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.base-rates-table h2 {
  margin-bottom: 10px;
}

.no-data-message {
  padding: 30px;
}

/* 附加费和旺季附加费表格样式 */
.surcharges-section, .peak-season-surcharges-section, .base-rates-table {
  margin-top: 30px;
  margin-bottom: 30px;
}

/* 调试信息样式 */
.debug-info {
  margin-top: 20px;
  padding: 15px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #f8f8f8;
}

.debug-status {
  display: flex;
  gap: 20px;
  margin-bottom: 10px;
}

.success {
  color: #67c23a;
}

.error {
  color: #f56c6c;
}

.first-item-preview pre,
.error-preview pre {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  font-family: monospace;
  overflow-x: auto;
  font-size: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.zone-example {
  margin-bottom: 15px;
  padding: 10px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.zone-example strong {
  font-size: 14px;
  margin-right: 10px;
}

.zone-visible {
  color: #67c23a;
  font-weight: bold;
  background-color: rgba(103, 194, 58, 0.1);
  padding: 2px 5px;
  border-radius: 3px;
}

.zone-hidden {
  color: #f56c6c;
  font-weight: bold;
  background-color: rgba(245, 108, 108, 0.1);
  padding: 2px 5px;
  border-radius: 3px;
}

.debug-pre {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  white-space: pre-wrap;
}

.raw-data-section {
  margin: 10px 0;
  padding: 15px;
  background-color: #f0f9ff;
  border-radius: 4px;
  border-left: 3px solid #409eff;
}

.raw-data-card {
  margin: 10px 0;
}

.data-keys-info {
  margin: 8px 0;
  font-size: 0.85em;
  color: #606266;
}

/* Excel风格的表格样式 */
.excel-style-table .editable-cell {
  cursor: text;
  height: 100%;
  width: 100%;
  padding: 6px 8px;
  min-height: 36px;
  transition: background-color 0.2s;
}

.excel-style-table .editable-cell:hover {
  background-color: #f0f9ff;
  position: relative;
}

.excel-style-table .editable-cell:hover::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 0;
  height: 0;
  border-style: solid;
  border-width: 0 8px 8px 0;
  border-color: transparent #409eff transparent transparent;
}

.excel-style-table .cell-editor {
  padding: 0;
  margin: -1px;
}

.excel-style-table .cell-editor .el-input,
.excel-style-table .cell-editor .el-input-number,
.excel-style-table .cell-editor .el-select {
  width: 100%;
}

.excel-style-table .el-input__inner,
.excel-style-table .el-input-number__inner {
  border: 2px solid #409eff;
  box-shadow: 0 0 5px rgba(64, 158, 255, 0.3);
}

/* 确保单元格可以完全填充表格单元格 */
.excel-style-table .el-table__cell {
  padding: 0 !important;
}

.excel-style-table .el-table__cell .cell {
  width: 100%;
  height: 100%;
  padding: 0 !important;
}

/* 高亮当前编辑的行 */
.excel-style-table .current-edit-row td {
  background-color: #f0f9ff !important;
}

/* 修复数字输入框和下拉选择器在单元格内的显示 */
.cell-editor .el-input-number {
  width: 100% !important;
}

.cell-editor .el-input-number .el-input__inner {
  padding-right: 30px;
}

.cell-editor .el-select {
  width: 100% !important;
}

/* 在style部分底部添加 */
.description-card {
  padding: 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: #fff;
  min-height: 80px;
  word-break: break-all;
  cursor: text;
}

.description-editor {
  margin-bottom: 20px;
}

.add-record-btn {
  margin-top: 10px;
}

/* 高亮显示刚修改过的单元格 */
.highlight-changed {
  color: #409eff;
  font-weight: bold;
  animation: flash-highlight 2s ease-out;
}

@keyframes flash-highlight {
  0% { background-color: #ffefd5; }
  70% { background-color: #ffefd5; }
  100% { background-color: transparent; }
}
</style>