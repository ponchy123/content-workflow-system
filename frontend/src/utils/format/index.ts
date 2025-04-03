/**
 * 单位转换与格式化常量定义
 */
// 货币相关常量
export const CURRENCY_CONSTANTS = {
  DEFAULT_CURRENCY: 'USD',
  DEFAULT_DECIMALS: 2,
  SYMBOLS: {
    'USD': '$',
    'CNY': '¥', 
    'EUR': '€',
    'GBP': '£',
    'JPY': '¥'
  } as Record<string, string>,
  LOCALE: 'zh-CN'
};

// 日期格式化常量
export const DATE_FORMAT_CONSTANTS = {
  DEFAULT_FORMAT: 'YYYY-MM-DD HH:mm:ss',
  DATE_ONLY: 'YYYY-MM-DD',
  TIME_ONLY: 'HH:mm:ss',
  MONTH_DAY: 'MM-DD',
  YEAR_MONTH: 'YYYY-MM'
};

// 体积重量计算常量
export const VOLUMETRIC_CONSTANTS = {
  // 体积重量计算系数
  CM_TO_KG_DIVISOR: 5000, // 长*宽*高(cm)/5000 = 体积重(kg)
  IN_TO_LB_DIVISOR: 139,  // 长*宽*高(in)/139 = 体积重(lb)
  IN_TO_LB_DIVISOR_ALT: 250, // 长*宽*高(in)/250 = 体积重(lb) (FedEx等使用)
  
  // 单位转换系数 
  CM_TO_IN: 2.54,    // 1英寸 = 2.54厘米
  KG_TO_LB: 2.20462, // 1千克 = 2.20462磅
  LB_TO_KG: 0.453592, // 1磅 = 0.453592千克
  OZ_TO_LB: 16       // 16盎司 = 1磅
};

// 尺寸单位显示
export const DIMENSION_UNIT_DISPLAY: Record<string, string> = {
  'in': '英寸',
  'cm': 'CM',
  'CM': 'CM'
};

// 重量单位显示
export const WEIGHT_UNIT_DISPLAY: Record<string, string> = {
  'lb': '磅',
  'KG': '公斤',
  'kg': '公斤',
  'OZ': '盎司',
  'oz': '盎司'
};

// 燃油费率默认值
export const DEFAULT_FUEL_RATE = 15; // 15%

/**
 * 格式化日期时间
 * @description 将 ISO 格式的日期字符串转换为指定格式的日期字符串
 * @param dateString - ISO 格式的日期字符串
 * @param format - 格式化模板，默认为 'YYYY-MM-DD HH:mm:ss'
 * @returns 格式化后的日期字符串
 * @example
 * ```ts
 * // 返回 "2023-01-01 12:30:00"
 * formatDateTime("2023-01-01T12:30:00Z")
 *
 * // 返回 "2023/01/01"
 * formatDateTime("2023-01-01T12:30:00Z", "YYYY/MM/DD")
 * ```
 */
export const formatDateTime = (dateString: string, format = DATE_FORMAT_CONSTANTS.DEFAULT_FORMAT): string => {
  if (!dateString) return '';

  const date = new Date(dateString);

  if (isNaN(date.getTime())) {
    return dateString;
  }

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');

  return format
    .replace('YYYY', String(year))
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds);
};

/**
 * 格式化金额
 * @description 将数值格式化为带货币符号的金额字符串
 * @param amount - 金额数值
 * @param currency - 货币代码，默认为 'USD'
 * @param decimals - 小数位数，默认为 2
 * @param showSymbol - 是否显示货币符号，默认为 true
 * @returns 格式化后的金额字符串
 * @example
 * ```ts
 * // 返回 "$1,000.00"
 * formatCurrency(1000)
 *
 * // 返回 "¥1,000.00"
 * formatCurrency(1000, "CNY")
 *
 * // 返回 "$1,000.0"
 * formatCurrency(1000, "USD", 1)
 * ```
 */
export const formatCurrency = (
  amount: number, 
  currency = CURRENCY_CONSTANTS.DEFAULT_CURRENCY, 
  decimals = CURRENCY_CONSTANTS.DEFAULT_DECIMALS, 
  showSymbol = true
): string => {
  if (amount === undefined || amount === null) return '';

  try {
    // 使用Intl.NumberFormat进行更标准的货币格式化
    return new Intl.NumberFormat(CURRENCY_CONSTANTS.LOCALE, {
      style: showSymbol ? 'currency' : 'decimal',
      currency: currency,
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(amount);
  } catch (error) {
    // 如果Intl.NumberFormat出错，回退到基本格式化
    console.warn('货币格式化失败，使用基本格式:', error);
    const formattedAmount = Number(amount).toFixed(decimals);
    const symbol = showSymbol ? (CURRENCY_CONSTANTS.SYMBOLS[currency] || currency) : '';
    return showSymbol ? `${symbol}${formattedAmount}` : formattedAmount;
  }
};

/**
 * 格式化文件大小
 * @description 将字节数转换为更易读的文件大小格式（如 KB, MB, GB 等）
 * @param bytes - 字节数
 * @returns 格式化后的文件大小字符串
 * @example
 * ```ts
 * // 返回 "1 KB"
 * formatFileSize(1024)
 *
 * // 返回 "1 MB"
 * formatFileSize(1048576)
 * ```
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * 格式化百分比
 * @description 将小数值（0-1之间）转换为百分比格式
 * @param value - 百分比值（0-1之间的小数）
 * @param decimals - 小数位数，默认为 2
 * @returns 格式化后的百分比字符串
 * @example
 * ```ts
 * // 返回 "50.00%"
 * formatPercent(0.5)
 *
 * // 返回 "50.5%"
 * formatPercent(0.505, 1)
 * ```
 */
export const formatPercent = (value: number, decimals = 2): string => {
  if (value === undefined || value === null) return '';

  return (value * 100).toFixed(decimals) + '%';
};
