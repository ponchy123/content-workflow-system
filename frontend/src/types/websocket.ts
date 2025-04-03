// WebSocket 消息类型
export interface TaskProgress {
  processed: number;
  total: number;
  status: 'processing' | 'completed' | 'failed';
}

// WebSocket 连接类型
export interface TaskProgressWebSocket {
  url: string;
  onmessage?: (event: MessageEvent) => void;
  onclose?: () => void;
  onerror?: (error: Event) => void;
}
