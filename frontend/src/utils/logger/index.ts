/**
 * 日志记录工具
 */

// 日志级别
export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
}

// 日志配置接口
export interface LoggerConfig {
  level: LogLevel;
  prefix?: string;
  enableTimestamp?: boolean;
  enableConsole?: boolean;
  customHandler?: (level: LogLevel, message: string, ...args: any[]) => void;
}

export class Logger {
  private config: LoggerConfig;

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = {
      level: LogLevel.INFO,
      prefix: '',
      enableTimestamp: true,
      enableConsole: true,
      ...config,
    };
  }

  private shouldLog(level: LogLevel): boolean {
    const levels = Object.values(LogLevel);
    const configLevelIndex = levels.indexOf(this.config.level);
    const currentLevelIndex = levels.indexOf(level);
    return currentLevelIndex >= configLevelIndex;
  }

  private formatMessage(level: LogLevel, message: string): string {
    const parts = [];

    if (this.config.enableTimestamp) {
      parts.push(new Date().toISOString());
    }

    if (this.config.prefix) {
      parts.push(this.config.prefix);
    }

    parts.push(`[${level}]`);
    parts.push(message);

    return parts.join(' ');
  }

  private log(level: LogLevel, message: string, ...args: any[]): void {
    if (!this.shouldLog(level)) {
      return;
    }

    const formattedMessage = this.formatMessage(level, message);

    if (this.config.customHandler) {
      this.config.customHandler(level, formattedMessage, ...args);
      return;
    }

    if (this.config.enableConsole) {
      switch (level) {
        case LogLevel.DEBUG:
          console.debug(formattedMessage, ...args);
          break;
        case LogLevel.INFO:
          console.info(formattedMessage, ...args);
          break;
        case LogLevel.WARN:
          console.warn(formattedMessage, ...args);
          break;
        case LogLevel.ERROR:
          console.error(formattedMessage, ...args);
          break;
      }
    }
  }

  debug(message: string, ...args: any[]): void {
    this.log(LogLevel.DEBUG, message, ...args);
  }

  info(message: string, ...args: any[]): void {
    this.log(LogLevel.INFO, message, ...args);
  }

  warn(message: string, ...args: any[]): void {
    this.log(LogLevel.WARN, message, ...args);
  }

  error(message: string, ...args: any[]): void {
    this.log(LogLevel.ERROR, message, ...args);
  }

  setConfig(config: Partial<LoggerConfig>): void {
    this.config = {
      ...this.config,
      ...config,
    };
  }

  getConfig(): LoggerConfig {
    return { ...this.config };
  }
}

// 创建默认日志实例
export const logger = new Logger({
  prefix: 'APP',
  level: process.env.NODE_ENV === 'production' ? LogLevel.INFO : LogLevel.DEBUG,
});

// 性能日志记录
export class PerformanceLogger {
  private startTime: number = 0;
  private marks: Map<string, number> = new Map();

  start(): void {
    this.startTime = performance.now();
    this.marks.clear();
  }

  mark(name: string): void {
    this.marks.set(name, performance.now());
  }

  end(name: string = 'default'): void {
    const endTime = performance.now();
    const duration = endTime - this.startTime;

    logger.info(`Performance [${name}] - Total duration: ${duration.toFixed(2)}ms`);

    this.marks.forEach((time, markName) => {
      const markDuration = time - this.startTime;
      logger.debug(`- ${markName}: ${markDuration.toFixed(2)}ms`);
    });
  }
}

// 创建默认性能日志实例
export const performanceLogger = new PerformanceLogger();
