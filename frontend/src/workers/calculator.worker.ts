// 计算器web worker
// 用于在后台线程执行复杂的运费计算操作

// 导入计算相关类型和工具
import type { CalculationRequest, CalculationResult, ChargeDetail } from '../types/calculator';
import { calculateFreightFormula, applyRules } from '../utils/calculator';

// Web Worker上下文
const ctx: Worker = self as any;

// 监听主线程消息
ctx.addEventListener('message', (event) => {
  try {
    const { type, payload, id } = event.data;
    
    switch (type) {
      case 'calculate':
        // 执行运费计算
        handleCalculation(payload, id);
        break;
        
      case 'batch_calculate':
        // 执行批量运费计算
        handleBatchCalculation(payload, id);
        break;
        
      default:
        // 未知操作类型
        ctx.postMessage({
          error: `未知的操作类型: ${type}`,
          id
        });
    }
  } catch (error) {
    // 处理异常
    ctx.postMessage({
      error: error instanceof Error ? error.message : '计算过程发生未知错误',
      id: event.data?.id
    });
  }
});

// 处理单次运费计算
async function handleCalculation(request: CalculationRequest, requestId: string) {
  try {
    // 模拟计算过程 (实际项目中会有真实的计算逻辑)
    // 1. 根据产品配置计算基础运费
    const baseCharge = calculateFreightFormula(request);
    
    // 2. 计算燃油附加费 (假设是基础运费的10%)
    const fuelSurcharge = parseFloat((baseCharge * 0.1).toFixed(2));
    
    // 4. 应用特殊规则
    const { finalRate, appliedRules } = applyRules(baseCharge, request);
    
    // 5. 生成计算明细
    const details = {
      weightCharge: parseFloat((request.weight * 10).toFixed(2)),
      distanceCharge: 30, // 假设固定值
      zoneCharge: 50, // 假设固定值
      volumeCharge: request.volume ? parseFloat((request.volume / 5000 * 10).toFixed(2)) : undefined,
      additionalCharges: [] as ChargeDetail[]
    };
    
    // 添加其他附加费 - 根据productType判断是否是危险品，而不是使用不存在的isDangerous属性
    if (request.productType.includes('dangerous')) {
      details.additionalCharges.push({
        name: '危险品处理费',
        amount: parseFloat((baseCharge * 0.5).toFixed(2)),
        type: 'dangerous',
        description: '危险品特殊处理费用'
      });
    }
    
    // 6. 汇总结果
    const result: CalculationResult = {
      requestId: requestId,
      baseCharge: baseCharge,
      fuelSurcharge: fuelSurcharge,
      totalCharge: parseFloat(finalRate.toFixed(2)),
      currency: 'CNY',
      details: details,
      status: 'success'
    };
    
    // 返回结果给主线程
    ctx.postMessage({ result, id: requestId });
  } catch (error) {
    ctx.postMessage({
      error: error instanceof Error ? error.message : '计算过程发生未知错误',
      id: requestId
    });
  }
}

// 处理批量运费计算
async function handleBatchCalculation(requests: CalculationRequest[], batchId: string) {
  try {
    // 处理批量请求
    const results = [];
    
    for (let i = 0; i < requests.length; i++) {
      const request = requests[i];
      // 对每个请求执行计算
      const baseCharge = calculateFreightFormula(request);
      const fuelSurcharge = parseFloat((baseCharge * 0.1).toFixed(2));
      // 应用特殊规则
      const { finalRate, appliedRules } = applyRules(baseCharge, request);
      
      // 生成唯一的请求ID
      const requestId = `${batchId}-${i}`;
      
      results.push({
        requestId,
        baseCharge,
        fuelSurcharge,
        totalCharge: parseFloat(finalRate.toFixed(2)),
        currency: 'CNY',
        estimatedDays: 3,
        details: {
          weightCharge: parseFloat((request.weight * 10).toFixed(2)),
          distanceCharge: 30,
          zoneCharge: 50,
          volumeCharge: request.volume ? parseFloat((request.volume / 5000 * 10).toFixed(2)) : undefined,
          additionalCharges: []
        },
        status: 'success'
      });
      
      // 为了避免UI冻结，每处理10个请求发送一次进度更新
      if ((i + 1) % 10 === 0 || i === requests.length - 1) {
        ctx.postMessage({
          progress: {
            current: i + 1,
            total: requests.length
          },
          id: batchId
        });
      }
    }
    
    // 返回全部结果
    ctx.postMessage({
      batchResults: results,
      id: batchId
    });
  } catch (error) {
    ctx.postMessage({
      error: error instanceof Error ? error.message : '批量计算过程发生未知错误',
      id: batchId
    });
  }
}

// 通知主线程worker已准备就绪
ctx.postMessage({ type: 'ready' }); 