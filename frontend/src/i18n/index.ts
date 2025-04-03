import { createI18n } from 'vue-i18n';
import { storage } from '@/utils/storage';
import zhCN from './locales/zh-CN';
import enUS from './locales/en-US';

const messages = {
  'zh-CN': zhCN,
  'en-US': enUS,
};

export type LocaleType = keyof typeof messages;

export const LOCALE_KEY = 'locale';
export const DEFAULT_LOCALE = 'zh-CN';

export const i18n = createI18n({
  legacy: false,
  locale: storage.get<LocaleType>(LOCALE_KEY) || DEFAULT_LOCALE,
  fallbackLocale: DEFAULT_LOCALE,
  messages,
});

export function setLocale(locale: LocaleType) {
  i18n.global.locale.value = locale;
  storage.set(LOCALE_KEY, locale);
  document.querySelector('html')?.setAttribute('lang', locale);
}

export function getLocale(): LocaleType {
  return i18n.global.locale.value as LocaleType;
}

// 动态加载语言包
export async function loadLocaleMessages(locale: LocaleType) {
  if (i18n.global.availableLocales.includes(locale)) {
    setLocale(locale);
    return;
  }

  try {
    const messages = await import(`./locales/${locale.replace('_', '-')}.ts`);
    i18n.global.setLocaleMessage(locale, messages.default);
    setLocale(locale);
  } catch (error) {
    console.error(`Failed to load locale messages for ${locale}`, error);
  }
}

// 注册 i18n 组件
export function setupI18n(app: any) {
  app.use(i18n);
}

// 导出 composable
export function useI18n() {
  return i18n.global;
}
