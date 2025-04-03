import dayjs from 'dayjs';

/**
 * 格式化日期
 * @param date 日期字符串或Date对象
 * @param format 格式化模板，默认为 YYYY-MM-DD HH:mm:ss
 * @returns 格式化后的日期字符串
 */
export const formatDate = (
  date: string | Date | undefined,
  format = 'YYYY-MM-DD HH:mm:ss',
): string => {
  if (!date) return '-';
  return dayjs(date).format(format);
};

/**
 * 获取相对时间
 * @param date 日期字符串或Date对象
 * @returns 相对时间字符串
 */
export const getRelativeTime = (date: string | Date | undefined): string => {
  if (!date) return '-';
  const now = dayjs();
  const target = dayjs(date);
  const diff = now.diff(target, 'second');

  if (diff < 60) {
    return '刚刚';
  } else if (diff < 3600) {
    return `${Math.floor(diff / 60)}分钟前`;
  } else if (diff < 86400) {
    return `${Math.floor(diff / 3600)}小时前`;
  } else if (diff < 2592000) {
    return `${Math.floor(diff / 86400)}天前`;
  } else if (diff < 31536000) {
    return `${Math.floor(diff / 2592000)}个月前`;
  } else {
    return `${Math.floor(diff / 31536000)}年前`;
  }
};

/**
 * 格式化日期和时间
 * @param dateTime 日期对象或日期字符串
 * @param format 格式字符串，默认为 'YYYY-MM-DD HH:mm:ss'
 * @returns 格式化后的日期时间字符串
 */
export const formatDateTime = (dateTime: Date | string, format: string = 'YYYY-MM-DD HH:mm:ss'): string => {
  return formatDate(dateTime, format);
};
