import { ref } from 'vue';
import { handleError, NetworkError } from '@/utils/logger/error-handler';

export interface TaskProgress {
  taskId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message?: string;
  result?: any;
}

export class TaskProgressWebSocket {
  private ws: WebSocket | null = null;
  private taskId: string;
  private baseUrl: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectTimeout = 1000;

  // 使用ref来存储进度状态，方便在组件中响应式使用
  public progress = ref<TaskProgress>({
    taskId: '',
    status: 'pending',
    progress: 0,
  });

  constructor(taskId: string) {
    this.taskId = taskId;
    this.baseUrl = `${import.meta.env.VITE_WS_BASE_URL}/ws/api/v1/calculator/task/${taskId}/`;
  }

  /**
   * 连接WebSocket
   */
  public connect(): void {
    try {
      this.ws = new WebSocket(this.baseUrl);
      this.setupEventHandlers();
    } catch (error) {
      handleError(new NetworkError('WebSocket连接失败'));
    }
  }

  /**
   * 设置WebSocket事件处理器
   */
  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket连接已建立');
      // 重置重连次数
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = event => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        console.error('解析WebSocket消息失败:', error);
      }
    };

    this.ws.onclose = event => {
      console.log('WebSocket连接已关闭:', event.code);
      this.handleReconnect();
    };

    this.ws.onerror = error => {
      handleError(new NetworkError('WebSocket错误'));
      this.handleReconnect();
    };
  }

  /**
   * 处理收到的消息
   */
  private handleMessage(data: any): void {
    // 更新进度状态
    this.progress.value = {
      taskId: this.taskId,
      status: data.status,
      progress: data.progress,
      message: data.message,
      result: data.result,
    };
  }

  /**
   * 处理重连逻辑
   */
  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

      setTimeout(() => {
        this.connect();
      }, this.reconnectTimeout * this.reconnectAttempts);
    } else {
      handleError(new NetworkError('WebSocket重连失败'));
    }
  }

  /**
   * 关闭WebSocket连接
   */
  public disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// 创建WebSocket连接的工厂函数
export function createTaskProgressWebSocket(taskId: string): TaskProgressWebSocket {
  const ws = new TaskProgressWebSocket(taskId);
  ws.connect();
  return ws;
}
