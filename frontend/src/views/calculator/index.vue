<template>
  <div class="freight-calculator">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>运费计算器</h2>
        </div>
      </template>

      <!-- 基本信息 -->
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane label="单票计算" name="single">
          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-width="120px"
            class="calculator-form"
          >
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="产品">
                  <el-select
                    v-model="form.productId"
                    placeholder="请选择产品"
                    @change="handleProductChange"
                  >
                    <el-option
                      v-for="product in products"
                      :key="product.id"
                      :label="product.name"
                      :value="product.id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="寄件邮编">
                  <el-input v-model="form.fromZip" placeholder="请输入寄件邮编" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="收件邮编">
                  <el-input v-model="form.toZip" placeholder="请输入收件邮编" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="重量(kg)">
                  <el-input-number v-model="form.weight" :min="0.1" :precision="2" />
                </el-form-item>
              </el-col>
              <el-col :span="16">
                <el-form-item label="尺寸(cm)">
                  <el-input-number v-model="form.length" :min="1" class="w-20" placeholder="长" />
                  <span class="mx-2">×</span>
                  <el-input-number v-model="form.width" :min="1" class="w-20" placeholder="宽" />
                  <span class="mx-2">×</span>
                  <el-input-number v-model="form.height" :min="1" class="w-20" placeholder="高" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item>
              <el-button type="primary" @click="calculateFee">计算运费</el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>

          <!-- 计算器组件 -->
          <template v-if="showCalculators">
            <div
              v-if="form.productId && form.fromZip && form.toZip && form.weight > 0"
              class="calculators mt-4"
            >
              <BaseFeeCalculator
                :product-id="form.productId"
                :weight="form.weight"
                :zone="String(zone)"
                @calculated="handleBaseFeeCalculated"
              />

              <SurchargeCalculator
                v-if="result.baseFee > 0"
                :product-id="form.productId"
                :weight="form.weight"
                :base-fee="result.baseFee"
                :zone="zone"
                :is-remote-area="isRemoteArea"
                @calculated="handleSurchargeCalculated"
              />

              <FuelRateCalculator
                v-if="result.baseFee > 0"
                :product-id="form.productId"
                :base-fee="result.baseFee"
                @calculated="handleFuelSurchargeCalculated"
              />
            </div>
          </template>

          <!-- 计算结果 -->
          <div v-if="result.total > 0" class="calculation-result mt-4">
            <el-descriptions title="计算结果" :column="2" border>
              <el-descriptions-item label="基础运费">
                {{ formatCurrency(result.baseFee) }}
              </el-descriptions-item>
              <el-descriptions-item label="燃油附加费">
                {{ formatCurrency(result.fuelSurcharge) }}
              </el-descriptions-item>
              <el-descriptions-item label="其他附加费">
                {{ formatCurrency(result.otherSurcharges) }}
              </el-descriptions-item>
              <el-descriptions-item label="总费用">
                <span class="text-xl font-bold text-primary">
                  {{ formatCurrency(result.total) }}
                </span>
              </el-descriptions-item>
            </el-descriptions>

            <!-- 费用明细 -->
            <el-collapse v-model="activeCollapse" class="mt-4">
              <el-collapse-item title="费用明细" name="detail">
                <el-table :data="result.details" border>
                  <el-table-column prop="name" label="费用项" />
                  <el-table-column prop="description" label="说明" />
                  <el-table-column prop="amount" label="金额">
                    <template #default="{ row }">
                      {{ formatCurrency(row.amount) }}
                    </template>
                  </el-table-column>
                </el-table>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-tab-pane>

        <el-tab-pane label="批量计算" name="batch">
          <BatchCalculator />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, watch } from 'vue';
  import { ElMessage } from 'element-plus';
  import type { FormInstance, FormRules, FormItemRule } from 'element-plus';
  import {
    BaseFeeCalculator,
    SurchargeCalculator,
    FuelRateCalculator,
    BatchCalculator,
  } from '@/components/calculator';

  interface Product {
    id: string;
    name: string;
  }

  // 表单数据
  const form = reactive({
    productId: '',
    fromZip: '',
    toZip: '',
    weight: 1,
    length: 1,
    width: 1,
    height: 1,
  });

  // 表单验证规则
  const rules: FormRules = {
    productId: [{ required: true, message: '请选择产品', trigger: 'change' }],
    fromZip: [{ required: true, message: '请输入寄件邮编', trigger: 'blur' }],
    toZip: [{ required: true, message: '请输入收件邮编', trigger: 'blur' }],
    weight: [{ required: true, type: 'number', min: 0.1, message: '请输入有效重量', trigger: 'blur' }]
  };

  // 产品列表
  const products = ref<Product[]>([]);
  
  // 获取产品信息的引用
  const product = ref<any>({
    currency: 'USD'
  });

  // 分区和偏远地区标识
  const zone = ref<number>(0);
  const isRemoteArea = ref(false);

  // 计算结果
  const result = reactive({
    baseFee: 0,
    fuelSurcharge: 0,
    otherSurcharges: 0,
    total: 0,
    details: [],
  });

  // 折叠面板激活项
  const activeCollapse = ref(['detail']);

  // 在 template 中添加标签页
  const activeTab = ref('single');

  // 显示计算器
  const showCalculators = ref(false);

  // 获取产品列表
  const fetchProducts = async () => {
    try {
      const response = await fetch('/api/products/active');
      products.value = await response.json();
    } catch (error) {
      ElMessage.error('获取产品列表失败');
    }
  };

  // 产品变更处理
  const handleProductChange = (productId: string) => {
    // TODO: 根据产品ID获取产品详情
  };

  // 计算运费
  const calculateFee = async () => {
    try {
      const response = await fetch('/api/calculator/calculate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(form),
      });

      if (!response.ok) {
        throw new Error('计算失败');
      }

      const data = await response.json();
      Object.assign(result, data);
    } catch (error) {
      ElMessage.error('运费计算失败');
    }
  };

  // 重置表单
  const resetForm = () => {
    Object.assign(form, {
      productId: '',
      fromZip: '',
      toZip: '',
      weight: 1,
      length: 1,
      width: 1,
      height: 1,
    });
    Object.assign(result, {
      baseFee: 0,
      fuelSurcharge: 0,
      otherSurcharges: 0,
      total: 0,
      details: [],
    });
  };

  // 格式化货币
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: product.value?.currency || 'USD',
    }).format(amount);
  };

  // 获取分区信息
  const fetchZoneInfo = async () => {
    try {
      const response = await fetch('/api/postal/zone', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          fromZip: form.fromZip,
          toZip: form.toZip,
        }),
      });

      const data = await response.json();
      zone.value = Number(data.zone);
      isRemoteArea.value = data.isRemoteArea;
    } catch (error) {
      console.error('获取分区信息失败:', error);
    }
  };

  // 处理基础运费计算结果
  const handleBaseFeeCalculated = (fee: number) => {
    result.baseFee = fee;
    updateTotal();
  };

  // 处理附加费计算结果
  const handleSurchargeCalculated = (fee: number) => {
    result.otherSurcharges = fee;
    updateTotal();
  };

  // 处理燃油附加费计算结果
  const handleFuelSurchargeCalculated = (fee: number) => {
    result.fuelSurcharge = fee;
    updateTotal();
  };

  // 更新总费用
  const updateTotal = () => {
    result.total = result.baseFee + result.fuelSurcharge + result.otherSurcharges;
  };

  // 监听邮编变化
  watch(
    () => [form.fromZip, form.toZip],
    async ([newFromZip, newToZip]) => {
      if (newFromZip && newToZip) {
        await fetchZoneInfo();
      }
    },
  );

  // 初始化
  fetchProducts();
</script>

<style scoped>
  .freight-calculator {
    padding: var(--el-spacing-base);
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h2 {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
    }
  }

  .calculator-form {
    max-width: 800px;
    margin: 0 auto;
    padding: var(--el-spacing-large);
    background-color: var(--el-bg-color);
    border-radius: var(--el-border-radius-base);
    box-shadow: var(--el-box-shadow-light);
    margin-bottom: 30px;

    :deep(.el-input-number) {
      width: 100%;
    }

    :deep(.el-select) {
      width: 100%;
    }

    :deep(.w-20) {
      width: 120px !important;
    }

    :deep(.mx-2) {
      margin: 0 8px;
    }
  }

  .calculators {
    margin-top: 40px;
    margin-bottom: 40px;
    display: flex;
    flex-direction: column;
    gap: var(--el-spacing-base);

    :deep(.el-card) {
      margin-bottom: 20px;
    }
  }

  .calculation-result {
    margin-top: 40px;
    padding: var(--el-spacing-base);
    border-radius: var(--el-border-radius-base);
    background-color: var(--el-bg-color);
    box-shadow: var(--el-box-shadow-light);

    :deep(.el-descriptions__title) {
      font-size: var(--el-font-size-large);
      color: var(--el-text-color-primary);
      margin-bottom: var(--el-spacing-base);
    }

    .text-xl {
      font-size: var(--el-font-size-extra-large);
    }

    .font-bold {
      font-weight: bold;
    }

    .text-primary {
      color: var(--el-color-primary);
    }

    .el-descriptions {
      margin-bottom: 20px;
    }

    .el-collapse {
      margin-top: 30px;
    }
  }

  :deep(.el-collapse) {
    border: 1px solid var(--el-border-color-light);
    border-radius: var(--el-border-radius-base);
    margin-top: var(--el-spacing-base);

    .el-collapse-item__header {
      font-size: var(--el-font-size-base);
      color: var(--el-text-color-primary);
      padding: var(--el-spacing-base);
    }

    .el-collapse-item__content {
      padding: var(--el-spacing-base);
    }
  }

  .calculator-view {
    .page-header {
      margin-bottom: var(--spacing-large);

      .page-title {
        font-size: var(--font-size-extra-large);
        font-weight: var(--font-weight-bold);
        color: var(--text-color-primary);
        margin-bottom: var(--spacing-base);
      }

      .page-description {
        color: var(--text-color-secondary);
        font-size: var(--font-size-base);
      }
    }

    .calculator-container {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: var(--spacing-large);

      @media (max-width: 1024px) {
        grid-template-columns: 1fr;
      }

      .calculator-section {
        background-color: var(--bg-color);
        border-radius: var(--border-radius-base);
        box-shadow: var(--box-shadow-light);

        .section-header {
          padding: var(--spacing-base);
          border-bottom: 1px solid var(--border-color);

          .title {
            font-size: var(--font-size-large);
            font-weight: var(--font-weight-medium);
            color: var(--text-color-primary);
          }
        }

        .section-body {
          padding: var(--spacing-large);
        }
      }

      .result-section {
        position: sticky;
        top: var(--spacing-large);

        .result-content {
          background-color: var(--bg-color-light);
          border-radius: var(--border-radius-base);
          padding: var(--spacing-base);
          margin-top: var(--spacing-base);

          .result-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: var(--spacing-small) 0;
            border-bottom: 1px solid var(--border-color-light);

            &:last-child {
              border-bottom: none;
            }

            .item-label {
              color: var(--text-color-regular);
            }

            .item-value {
              font-weight: var(--font-weight-medium);
              color: var(--text-color-primary);

              &.highlight {
                color: var(--color-primary);
                font-size: var(--font-size-large);
              }
            }
          }
        }
      }
    }

    .history-section {
      margin-top: var(--spacing-extra-large);

      .history-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--spacing-base);

        .title {
          font-size: var(--font-size-large);
          font-weight: var(--font-weight-medium);
          color: var(--text-color-primary);
        }

        .actions {
          display: flex;
          gap: var(--spacing-base);
        }
      }
    }
  }

  :deep(.el-tabs__content) {
    padding: 20px;
  }

  :deep(.el-form-item) {
    margin-bottom: 22px;
  }

  .mt-4 {
    margin-top: 24px !important;
  }
</style>
