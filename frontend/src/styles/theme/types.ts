export type ThemeMode = 'light' | 'dark' | 'system';

export interface ThemeToken {
  // 颜色
  colorPrimary: string;
  colorSuccess: string;
  colorWarning: string;
  colorError: string;
  colorInfo: string;
  colorTextPrimary: string;
  colorTextRegular: string;
  colorTextSecondary: string;
  colorBorder: string;
  colorBorderLight: string;
  colorBackground: string;
  colorBackgroundPage: string;

  // 间距
  spacingMini: string;
  spacingSmall: string;
  spacingBase: string;
  spacingLarge: string;
  spacingXl: string;

  // 圆角
  borderRadiusSmall: string;
  borderRadiusBase: string;
  borderRadiusLarge: string;

  // 阴影
  boxShadow: string;
  boxShadowLight: string;
  boxShadowDark: string;
  boxShadowHover: string;

  // 响应式断点
  breakpointSm: string;
  breakpointMd: string;
  breakpointLg: string;
  breakpointXl: string;

  // 组件尺寸
  headerHeight: string;
  sidebarWidth: string;
  sidebarCollapsedWidth: string;
  toolbarHeight: string;
  tabbarHeight: string;
  footerHeight: string;
  cardPadding: string;
  tablePadding: string;
  formLabelWidth: string;
  formItemMargin: string;
  inputHeight: string;
  buttonHeight: string;
  buttonPadding: string;
}

export interface ThemeConfig {
  mode: ThemeMode;
  token: ThemeToken;
}

export interface Theme {
  colors: {
    primary: string;
    success: string;
    warning: string;
    danger: string;
    info: string;
    text: {
      primary: string;
      regular: string;
      secondary: string;
      placeholder: string;
      disabled: string;
    };
    border: {
      base: string;
      light: string;
      lighter: string;
      dark: string;
    };
    background: {
      base: string;
      page: string;
      overlay: string;
      light: string;
      lighter: string;
    };
  };
  spacing: {
    mini: string;
    small: string;
    base: string;
    large: string;
    extraLarge: string;
    component: {
      cardPadding: string;
      formItem: string;
      section: string;
    };
    layout: {
      gutter: string;
      margin: string;
      padding: string;
    };
  };
  typography: {
    fontFamily: {
      base: string;
      code: string;
    };
    fontSize: {
      mini: string;
      small: string;
      base: string;
      medium: string;
      large: string;
      extraLarge: string;
    };
    fontWeight: {
      regular: string;
      medium: string;
      semibold: string;
      bold: string;
    };
    lineHeight: {
      tight: string;
      normal: string;
      relaxed: string;
    };
  };
  borderRadius: {
    small: string;
    base: string;
    large: string;
    circle: string;
  };
  boxShadow: {
    light: string;
    base: string;
    dark: string;
  };
  transition: {
    duration: string;
    function: string;
  };
  zIndex: {
    dropdown: string;
    sticky: string;
    fixed: string;
    modalBackdrop: string;
    modal: string;
    popover: string;
    tooltip: string;
  };
  layout: {
    headerHeight: string;
    sidebarWidth: string;
    sidebarCollapsedWidth: string;
  };
  component: {
    formLabelWidth: string;
    tableHeaderBg: string;
  };
}
