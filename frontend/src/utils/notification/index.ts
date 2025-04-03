import type { Notification } from '@/types/notification';
import { useNotificationConfig } from '@/stores/notification/config';

interface NotificationSoundConfig {
  success: string;
  warning: string;
  info: string;
  error: string;
}

class NotificationManager {
  private audioCache: Map<string, HTMLAudioElement> = new Map();
  private notificationPermission: NotificationPermission = 'default';
  private notificationQueue: Notification[] = [];
  private isProcessingQueue = false;
  private readonly soundConfig: NotificationSoundConfig = {
    success: '/sounds/success.mp3',
    warning: '/sounds/warning.mp3',
    info: '/sounds/info.mp3',
    error: '/sounds/error.mp3',
  };

  constructor() {
    // 预加载所有通知音效
    Object.entries(this.soundConfig).forEach(([type, path]) => {
      const audio = new Audio(path);
      audio.preload = 'auto';
      this.audioCache.set(type, audio);
    });

    // 请求桌面通知权限
    if ('Notification' in window) {
      Notification.requestPermission().then(permission => {
        this.notificationPermission = permission;
        if (permission === 'granted') {
          this.processNotificationQueue();
        }
      });
    }
  }

  async playSound(soundPath: string): Promise<void> {
    try {
      let audio = this.audioCache.get(soundPath);
      if (!audio) {
        audio = new Audio(soundPath);
        this.audioCache.set(soundPath, audio);
      }
      await audio.play();
    } catch (error) {
      console.error('播放通知音效失败:', error);
    }
  }

  async showDesktopNotification(notification: Notification): Promise<void> {
    if (!('Notification' in window)) {
      return;
    }

    try {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        new Notification(notification.title, {
          body: notification.message,
          icon: '/icons/notification.png',
        });
      }
    } catch (error) {
      console.error('显示桌面通知失败:', error);
    }
  }

  private async processNotificationQueue() {
    if (this.isProcessingQueue || this.notificationQueue.length === 0) {
      return;
    }

    this.isProcessingQueue = true;
    try {
      while (this.notificationQueue.length > 0) {
        const notification = this.notificationQueue.shift();
        if (notification) {
          await this.showDesktopNotification(notification);
          // 添加延迟以避免通知重叠
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      }
    } finally {
      this.isProcessingQueue = false;
    }
  }

  async handleNewNotification(notification: Notification): Promise<void> {
    const configStore = useNotificationConfig();
    const { soundEnabled, desktopNotification } = configStore.config;

    if (soundEnabled) {
      const soundType = notification.type === 'error' ? 'error' :
                       notification.type === 'warning' ? 'warning' :
                       notification.type === 'system' ? 'info' : 'success';
      await this.playSound(this.soundConfig[soundType]);
    }

    if (desktopNotification) {
      if (document.visibilityState === 'visible') {
        // 如果页面可见，使用普通的通知
        await this.showDesktopNotification(notification);
      } else {
        // 如果页面不可见，将通知加入队列
        this.notificationQueue.push(notification);
        await this.processNotificationQueue();
      }
    }
  }

  // 清理资源
  dispose() {
    this.audioCache.forEach(audio => {
      audio.src = '';
    });
    this.audioCache.clear();
    this.notificationQueue = [];
  }
}

export const notificationManager = new NotificationManager();

// 格式化通知时间
export function formatNotificationTime(time: string | Date): string {
  const date = new Date(time);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (minutes < 1) {
    return '刚刚';
  } else if (minutes < 60) {
    return `${minutes}分钟前`;
  } else if (hours < 24) {
    return `${hours}小时前`;
  } else if (days < 7) {
    return `${days}天前`;
  } else {
    return date.toLocaleDateString();
  }
}

// 通知服务类
export class NotificationService {
  private static instance: NotificationService;

  private constructor() {}

  static getInstance(): NotificationService {
    if (!NotificationService.instance) {
      NotificationService.instance = new NotificationService();
    }
    return NotificationService.instance;
  }

  // 显示通知
  showNotification(notification: Notification): void {
    notificationManager.handleNewNotification(notification);
  }

  // 清理资源
  dispose(): void {
    notificationManager.dispose();
  }
}

// 导出单例实例
export const notificationService = NotificationService.getInstance();
