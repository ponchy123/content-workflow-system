import { Theme } from './types';

export const lightTheme: Theme = {
  colors: {
    primary: 'var(--color-primary)',
    success: 'var(--color-success)',
    warning: 'var(--color-warning)',
    danger: 'var(--color-danger)',
    info: 'var(--color-info)',
    text: {
      primary: 'var(--text-color-primary)',
      regular: 'var(--text-color-regular)',
      secondary: 'var(--text-color-secondary)',
      placeholder: 'var(--text-color-placeholder)',
      disabled: 'var(--text-color-disabled)',
    },
    border: {
      base: 'var(--border-color)',
      light: 'var(--border-color-light)',
      lighter: 'var(--border-color-lighter)',
      dark: 'var(--border-color-dark)',
    },
    background: {
      base: 'var(--bg-color)',
      page: 'var(--bg-color-page)',
      overlay: 'var(--bg-color-overlay)',
      light: 'var(--bg-color-light)',
      lighter: 'var(--bg-color-lighter)',
    },
  },
  spacing: {
    mini: 'var(--spacing-mini)',
    small: 'var(--spacing-small)',
    base: 'var(--spacing-base)',
    large: 'var(--spacing-large)',
    extraLarge: 'var(--spacing-extra-large)',
    component: {
      cardPadding: 'var(--spacing-card-padding)',
      formItem: 'var(--spacing-form-item)',
      section: 'var(--spacing-section)',
    },
    layout: {
      gutter: 'var(--spacing-layout-gutter)',
      margin: 'var(--spacing-layout-margin)',
      padding: 'var(--spacing-layout-padding)',
    },
  },
  typography: {
    fontFamily: {
      base: 'var(--font-family-base)',
      code: 'var(--font-family-code)',
    },
    fontSize: {
      mini: 'var(--font-size-mini)',
      small: 'var(--font-size-small)',
      base: 'var(--font-size-base)',
      medium: 'var(--font-size-medium)',
      large: 'var(--font-size-large)',
      extraLarge: 'var(--font-size-extra-large)',
    },
    fontWeight: {
      regular: 'var(--font-weight-regular)',
      medium: 'var(--font-weight-medium)',
      semibold: 'var(--font-weight-semibold)',
      bold: 'var(--font-weight-bold)',
    },
    lineHeight: {
      tight: 'var(--line-height-tight)',
      normal: 'var(--line-height-normal)',
      relaxed: 'var(--line-height-relaxed)',
    },
  },
  borderRadius: {
    small: 'var(--border-radius-small)',
    base: 'var(--border-radius-base)',
    large: 'var(--border-radius-large)',
    circle: 'var(--border-radius-circle)',
  },
  boxShadow: {
    light: 'var(--box-shadow-light)',
    base: 'var(--box-shadow)',
    dark: 'var(--box-shadow-dark)',
  },
  transition: {
    duration: 'var(--transition-duration)',
    function: 'var(--transition-function)',
  },
  zIndex: {
    dropdown: 'var(--z-index-dropdown)',
    sticky: 'var(--z-index-sticky)',
    fixed: 'var(--z-index-fixed)',
    modalBackdrop: 'var(--z-index-modal-backdrop)',
    modal: 'var(--z-index-modal)',
    popover: 'var(--z-index-popover)',
    tooltip: 'var(--z-index-tooltip)',
  },
  layout: {
    headerHeight: 'var(--layout-header-height)',
    sidebarWidth: 'var(--layout-sidebar-width)',
    sidebarCollapsedWidth: 'var(--layout-sidebar-collapsed-width)',
  },
  component: {
    formLabelWidth: 'var(--form-label-width)',
    tableHeaderBg: 'var(--table-header-bg)',
  },
};

export const darkTheme: Theme = {
  ...lightTheme,
  colors: {
    ...lightTheme.colors,
    text: {
      primary: 'var(--dark-text-color-primary)',
      regular: 'var(--dark-text-color-regular)',
      secondary: 'var(--dark-text-color-secondary)',
      placeholder: 'var(--dark-text-color-placeholder)',
      disabled: 'var(--dark-text-color-disabled)',
    },
    border: {
      base: 'var(--dark-border-color)',
      light: 'var(--dark-border-color-light)',
      lighter: 'var(--dark-border-color-lighter)',
      dark: 'var(--dark-border-color-dark)',
    },
    background: {
      base: 'var(--dark-bg-color)',
      page: 'var(--dark-bg-color-page)',
      overlay: 'var(--dark-bg-color-overlay)',
      light: 'var(--dark-bg-color-light)',
      lighter: 'var(--dark-bg-color-lighter)',
    },
  },
  boxShadow: {
    light: 'var(--dark-box-shadow-light)',
    base: 'var(--dark-box-shadow)',
    dark: 'var(--dark-box-shadow-dark)',
  },
  component: {
    ...lightTheme.component,
    tableHeaderBg: 'var(--dark-table-header-bg)',
  },
};
