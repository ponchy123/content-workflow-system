/**
 * 邮编与偏远地区相关的工具函数
 */

/**
 * 检查两个偏远地区描述是否匹配
 * @param remoteLevel 偏远地区等级（来自偏远地区数据库）
 * @param conditionDescription 附加费条件描述（来自产品附加费）
 * @returns 是否匹配
 */
export function isRemoteLevelMatch(remoteLevel: string, conditionDescription: string): boolean {
  if (!remoteLevel || !conditionDescription) return false;
  
  // 完全相等情况，最优先匹配
  if (remoteLevel === conditionDescription) return true;
  
  // 清理和规范化文本以便比较
  const normalizeText = (text: string): string => {
    return text.toLowerCase()
      .replace(/\s+/g, '')
      .replace(/[()（）]/g, '')
      .replace(/fedex/gi, '')
      .replace(/ground/gi, '')
      .replace(/home\s*delivery/gi, '')
      .trim();
  };
  
  const normalizedRemote = normalizeText(remoteLevel);
  const normalizedCondition = normalizeText(conditionDescription);
  
  // 如果规范化后相等，则匹配
  if (normalizedRemote === normalizedCondition) return true;
  
  // 包含关系检查
  if (normalizedRemote.includes(normalizedCondition) || 
      normalizedCondition.includes(normalizedRemote)) {
    return true;
  }
  
  // 关键词匹配
  const remoteKeywords = [
    '偏远', 'remote', 'das', 'delivery area surcharge',
    '商业', 'commercial', 'comm', 
    '住宅', 'residential', 'resi',
    '扩展', 'extended', 'ext',
    '一级', '1级', 'level1',
    '二级', '2级', 'level2', 
    '三级', '3级', 'level3',
    '特殊', 'special',
    '极偏远', 'extreme remote'
  ];
  
  // 提取关键词
  const extractedRemoteKeywords = remoteKeywords.filter(keyword => 
    normalizedRemote.includes(normalizeText(keyword))
  );
  
  const extractedConditionKeywords = remoteKeywords.filter(keyword => 
    normalizedCondition.includes(normalizeText(keyword))
  );
  
  // 检查关键词是否有重叠
  const hasCommonKeywords = extractedRemoteKeywords.some(keyword => 
    extractedConditionKeywords.includes(keyword)
  );
  
  return hasCommonKeywords;
}

/**
 * 获取偏远地区等级的类型
 * @param level 偏远地区等级
 * @returns 标签类型
 */
export function getRemoteLevelType(level: string): 'info' | 'warning' | 'danger' | 'success' {
  if (!level) return 'info';
  
  if (level.includes('一级') || level.includes('1级') || 
      level.includes('商业地址偏远地区配送') || 
      level.includes('Commercial(FedEx Ground)')) {
    return 'info';
  } else if (level.includes('二级') || level.includes('2级') || 
             level.includes('商业地址扩展偏远地区配送') || 
             level.includes('Extended Commercial(FedEx Ground)')) {
    return 'warning';
  } else if (level.includes('三级') || level.includes('3级') || 
             level.includes('住宅地址偏远地区配送') || 
             level.includes('Residential(FedEx Ground)') || 
             level.includes('特殊')) {
    return 'danger';
  } else if (level.includes('住宅地址扩展偏远地区配送') || 
             level.includes('Extended Residential') || 
             level.includes('Home Delivery')) {
    return 'danger';
  } else if (level.includes('极偏远')) {
    return 'danger';
  } else {
    return 'success';
  }
}

/**
 * 根据产品的偏远附加费列表和偏远地区等级，查找匹配的附加费
 * @param surcharges 产品附加费列表
 * @param remoteLevel 偏远地区等级
 * @returns 匹配的附加费，如果没有匹配则返回null
 */
export function findMatchingRemoteSurcharge(surcharges: any[], remoteLevel: string): any | null {
  if (!surcharges || !surcharges.length || !remoteLevel) return null;
  
  // 筛选出偏远地区附加费
  const remoteSurcharges = surcharges.filter(
    s => s.surcharge_type === 'DELIVERY_AREA_SURCHARGE' || 
         s.name?.includes('偏远地区') || 
         s.name?.includes('DAS Remote')
  );
  
  if (!remoteSurcharges.length) return null;
  
  // 首先尝试完全匹配
  let matchedSurcharge = remoteSurcharges.find(
    s => s.condition_description === remoteLevel
  );
  
  // 如果没有完全匹配，尝试使用辅助函数匹配
  if (!matchedSurcharge) {
    matchedSurcharge = remoteSurcharges.find(
      s => isRemoteLevelMatch(remoteLevel, s.condition_description)
    );
  }
  
  return matchedSurcharge;
} 