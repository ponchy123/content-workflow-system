import type { ThemeToken } from './types';
import { Theme } from './types';
import { lightTheme, darkTheme } from './themes';

export function generateCssVariables(theme: Theme): Record<string, string> {
  const cssVars: Record<string, string> = {};

  // 处理嵌套对象
  const processNestedObject = (obj: any, prefix: string = '') => {
    Object.entries(obj).forEach(([key, value]) => {
      if (typeof value === 'object') {
        processNestedObject(value, `${prefix}${key}-`);
      } else if (typeof value === 'string') {
        cssVars[`--${prefix}${key}`] = value;
      }
    });
  };

  processNestedObject(theme);
  return cssVars;
}

export function applyCssVariables(
  vars: Record<string, string>,
  element = document.documentElement,
) {
  Object.entries(vars).forEach(([prop, value]) => {
    element.style.setProperty(prop, value);
  });
}

export function getCssVariable(name: keyof ThemeToken, element = document.documentElement): string {
  const cssKey = name.replace(/([A-Z])/g, '-$1').toLowerCase();
  return getComputedStyle(element).getPropertyValue(`--${cssKey}`).trim();
}

export function isDarkMode(): boolean {
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

export function watchSystemTheme(callback: (isDark: boolean) => void): () => void {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  const listener = (e: MediaQueryListEvent) => callback(e.matches);
  mediaQuery.addEventListener('change', listener);
  return () => mediaQuery.removeEventListener('change', listener);
}

/**
 * 应用主题到文档根元素
 * @param theme 主题配置
 */
export function applyTheme(theme: Theme): void {
  const root = document.documentElement;

  // 颜色
  Object.entries(theme.colors).forEach(([key, value]) => {
    if (typeof value === 'object') {
      Object.entries(value).forEach(([subKey, subValue]) => {
        root.style.setProperty(`--${key}-${subKey}`, subValue);
      });
    } else {
      root.style.setProperty(`--color-${key}`, value);
    }
  });

  // 间距
  Object.entries(theme.spacing).forEach(([key, value]) => {
    if (typeof value === 'object') {
      Object.entries(value).forEach(([subKey, subValue]) => {
        root.style.setProperty(`--spacing-${key}-${subKey}`, subValue);
      });
    } else {
      root.style.setProperty(`--spacing-${key}`, value);
    }
  });

  // 字体
  Object.entries(theme.typography).forEach(([key, value]) => {
    if (typeof value === 'object') {
      Object.entries(value).forEach(([subKey, subValue]) => {
        root.style.setProperty(`--${key}-${subKey}`, subValue);
      });
    }
  });

  // 圆角
  Object.entries(theme.borderRadius).forEach(([key, value]) => {
    root.style.setProperty(`--border-radius-${key}`, value);
  });

  // 阴影
  Object.entries(theme.boxShadow).forEach(([key, value]) => {
    root.style.setProperty(`--box-shadow-${key}`, value);
  });

  // 过渡
  Object.entries(theme.transition).forEach(([key, value]) => {
    root.style.setProperty(`--transition-${key}`, value);
  });

  // z-index
  Object.entries(theme.zIndex).forEach(([key, value]) => {
    root.style.setProperty(`--z-index-${key}`, value);
  });

  // 布局
  Object.entries(theme.layout).forEach(([key, value]) => {
    root.style.setProperty(`--layout-${key}`, value);
  });

  // 组件
  Object.entries(theme.component).forEach(([key, value]) => {
    root.style.setProperty(`--${key}`, value);
  });
}

/**
 * 切换主题
 * @param isDark 是否为暗色主题
 */
export function toggleTheme(isDark: boolean): void {
  applyTheme(isDark ? darkTheme : lightTheme);
  document.documentElement.classList.toggle('dark', isDark);
}

/**
 * 获取当前主题
 * @returns 当前主题配置
 */
export function getCurrentTheme(): Theme {
  return document.documentElement.classList.contains('dark') ? darkTheme : lightTheme;
}

/**
 * 初始化主题
 * 根据系统主题偏好设置初始主题
 */
export function initTheme(): void {
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  toggleTheme(prefersDark);

  // 监听系统主题变化
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
    toggleTheme(e.matches);
  });
}
