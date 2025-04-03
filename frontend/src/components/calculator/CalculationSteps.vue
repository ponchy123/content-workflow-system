<template>
  <div class="calculation-steps">
    <div class="steps-header">
      <h4>{{ title }}</h4>
    </div>
    <el-steps :active="steps.length" direction="vertical">
      <el-step v-for="(step, index) in steps" :key="index" :title="step.description">
        <template #description>
          <div class="step-formula">
            <el-tag size="small" type="info">计算公式</el-tag>
            <div class="formula-content" v-html="formatFormula(step.formula)" />
          </div>
          <div v-if="step.result" class="step-result">
            <el-tag size="small" type="success">计算结果</el-tag>
            <div class="result-content">{{ formatCurrency(step.result) }}</div>
          </div>
        </template>
      </el-step>
    </el-steps>
  </div>
</template>

<script setup lang="ts">
  interface CalculationStep {
    description: string;
    formula: string;
    result?: number;
  }

  const props = defineProps<{
    title?: string;
    steps: CalculationStep[];
  }>();

  // 格式化公式，将数学符号转换为 HTML 实体
  const formatFormula = (formula: string) => {
    return formula
      .replace(/\*/g, '×')
      .replace(/\//g, '÷')
      .replace(/\+/g, ' + ')
      .replace(/-/g, ' - ')
      .replace(/\(/g, '（')
      .replace(/\)/g, '）');
  };

  // 格式化货币
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
    }).format(amount);
  };
</script>

<style scoped>
  .calculation-steps {
    margin-top: var(--spacing-large);
    padding: var(--spacing-base);
    background-color: var(--bg-color-page);
    border-radius: var(--border-radius-base);
  }

  .steps-header {
    margin-bottom: var(--spacing-base);
  }

  .steps-header h4 {
    margin: 0;
    font-size: var(--font-size-medium);
    font-weight: var(--font-weight-bold);
    color: var(--text-color-primary);
  }

  .step-formula,
  .step-result {
    margin-top: var(--spacing-small);
  }

  .formula-content,
  .result-content {
    margin-top: var(--spacing-mini);
    padding: var(--spacing-small);
    background-color: var(--bg-color);
    border-radius: var(--border-radius-small);
    font-family: var(--font-family-monospace, monospace);
    color: var(--text-color-regular);
  }

  .result-content {
    color: var(--color-success);
    font-weight: var(--font-weight-bold);
  }

  :deep(.el-step__description) {
    padding-right: var(--spacing-base);
  }

  :deep(.el-step__head) {
    background-color: var(--bg-color-page);
  }
</style>
