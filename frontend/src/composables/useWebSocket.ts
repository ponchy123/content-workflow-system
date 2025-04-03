import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useNotificationStore } from '@/stores/notification/notification';
import pako from 'pako';

interface WebSocketOptions {
  maxReconnectAttempts?: number;
  initialReconnectDelay?: number;
  maxReconnectDelay?: number;
  reconnectBackoffMultiplier?: number;
  heartbeatInterval?: number;
  connectionTimeout?: number;
  maxQueueSize?: number;
  compressionThreshold?: number;
}

interface QueuedMessage {
  id: string;
  data: any;
  timestamp: number;
  retries: number;
  maxRetries: number;
  priority: number;
  compressed?: boolean;
  requiresAck?: boolean;
  ackTimeout?: number;
  onAck?: (value: any) => void;
  onTimeout?: (reason?: any) => void;
}

// 消息确认管理
const pendingAcks = new Map<
  string,
  {
    message: QueuedMessage;
    timeoutId: number;
  }
>();

// 生成消息ID
const generateMessageId = () => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

// 处理消息确认
const handleMessageAck = (messageId: string) => {
  const pending = pendingAcks.get(messageId);
  if (pending) {
    clearTimeout(pending.timeoutId);
    pending.message.onAck?.(true);
    pendingAcks.delete(messageId);
  }
};

// 优化的心跳配置
const HEARTBEAT_CONFIG = {
  initialDelay: 1000,
  maxDelay: 30000,
  factor: 1.5,
  jitter: 100,
};

// 自适应心跳间隔计算
const calculateNextHeartbeatInterval = (currentInterval: number) => {
  const nextInterval = currentInterval * HEARTBEAT_CONFIG.factor;
  const jitter = Math.random() * HEARTBEAT_CONFIG.jitter;
  return Math.min(nextInterval + jitter, HEARTBEAT_CONFIG.maxDelay);
};

export const useWebSocket = (options: WebSocketOptions = {}) => {
  const {
    maxReconnectAttempts = 5,
    initialReconnectDelay = 1000,
    maxReconnectDelay = 30000,
    reconnectBackoffMultiplier = 2,
    heartbeatInterval = 30000,
    connectionTimeout = 5000,
    maxQueueSize = 100,
    compressionThreshold = 1024, // 1KB
  } = options;

  const ws = ref<WebSocket | null>(null);
  const isConnected = ref(false);
  const notificationStore = useNotificationStore();
  const reconnectTimeout = ref<number | null>(null);
  const heartbeatTimeout = ref<number | null>(null);
  const connectionTimeoutId = ref<number | null>(null);
  const reconnectAttempts = ref(0);
  const forceClosed = ref(false);
  const messageQueue = ref<QueuedMessage[]>([]);
  const lastHeartbeatResponse = ref<number>(0);
  const isReconnecting = ref(false);
  const keepAliveInterval = ref<number | null>(null);

  // 消息压缩
  const compressMessage = (data: any): { compressed: boolean; data: string } => {
    try {
      const jsonStr = JSON.stringify(data);
      if (jsonStr.length < compressionThreshold) {
        return { compressed: false, data: jsonStr };
      }
      const compressed = pako.deflate(jsonStr);
      const base64 = btoa(String.fromCharCode.apply(null, [...compressed]));
      return { compressed: true, data: base64 };
    } catch (error) {
      console.error('压缩消息失败:', error);
      return { compressed: false, data: JSON.stringify(data) };
    }
  };

  const decompressMessage = (data: string, isCompressed: boolean): any => {
    try {
      if (!isCompressed) {
        return JSON.parse(data);
      }
      const binary = atob(data);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
      }
      const decompressed = pako.inflate(bytes, { to: 'string' });
      return JSON.parse(decompressed);
    } catch (error) {
      console.error('解压消息失败:', error);
      return JSON.parse(data);
    }
  };

  // 连接保活
  const startKeepAlive = () => {
    if (keepAliveInterval.value) {
      clearInterval(keepAliveInterval.value);
    }
    keepAliveInterval.value = window.setInterval(() => {
      const now = Date.now();
      if (now - lastHeartbeatResponse.value > heartbeatInterval * 2) {
        console.warn('连接可能已断开，尝试重连');
        ws.value?.close();
        connect();
      }
    }, heartbeatInterval);
  };

  const stopKeepAlive = () => {
    if (keepAliveInterval.value) {
      clearInterval(keepAliveInterval.value);
      keepAliveInterval.value = null;
    }
  };

  // 消息重试
  const retryFailedMessages = () => {
    const now = Date.now();
    messageQueue.value = messageQueue.value.filter(msg => {
      if (msg.retries < msg.maxRetries && now - msg.timestamp < 5 * 60 * 1000) {
        send(msg.data, msg.priority);
        msg.retries++;
        return true;
      }
      return false;
    });
  };

  const processMessageQueue = async () => {
    if (!isConnected.value || messageQueue.value.length === 0) {
      return;
    }

    // 按优先级排序
    messageQueue.value.sort((a, b) => b.priority - a.priority);

    const now = Date.now();
    const messages = [...messageQueue.value];
    messageQueue.value = [];

    for (const message of messages) {
      if (now - message.timestamp > 5 * 60 * 1000) {
        continue;
      }

      if (message.retries >= message.maxRetries) {
        console.warn('消息重试次数超过限制:', message.data);
        continue;
      }

      try {
        await send(message.data, message.priority);
      } catch (error) {
        message.retries++;
        messageQueue.value.push(message);
      }
    }
  };

  // 增强的消息发送函数
  const send = async (data: any, priority: number = 1, requiresAck: boolean = false) => {
    const messageId = generateMessageId();
    const message: QueuedMessage = {
      id: messageId,
      data,
      timestamp: Date.now(),
      retries: 0,
      maxRetries: 3,
      priority,
      requiresAck,
    };

    if (ws.value?.readyState === WebSocket.OPEN) {
      try {
        const { compressed, data: processedData } = compressMessage(data);
        const messagePayload = {
          id: messageId,
          data: processedData,
          compressed,
          priority,
          timestamp: Date.now(),
          requiresAck,
        };

        ws.value.send(JSON.stringify(messagePayload));

        if (requiresAck) {
          return new Promise((resolve, reject) => {
            const timeoutId = window.setTimeout(() => {
              pendingAcks.delete(messageId);
              message.onTimeout?.();
              reject(new Error('消息确认超时'));
            }, 5000);

            message.onAck = resolve;
            message.onTimeout = reject;
            pendingAcks.set(messageId, { message, timeoutId });
          });
        }

        return true;
      } catch (error) {
        console.error('发送消息失败:', error);
        return false;
      }
    } else {
      if (messageQueue.value.length < maxQueueSize) {
        messageQueue.value.push(message);
        messageQueue.value.sort((a, b) => b.priority - a.priority);
      } else {
        console.error('消息队列已满，丢弃消息:', data);
      }
      return false;
    }
  };

  // 增强的消息处理
  const handleMessage = (event: MessageEvent) => {
    try {
      const rawData = JSON.parse(event.data);

      // 处理消息确认
      if (rawData.type === 'ack') {
        handleMessageAck(rawData.messageId);
        return;
      }

      const data = decompressMessage(rawData.data, rawData.compressed);

      // 发送确认回执
      if (rawData.requiresAck && ws.value?.readyState === WebSocket.OPEN) {
        ws.value.send(
          JSON.stringify({
            type: 'ack',
            messageId: rawData.id,
            timestamp: Date.now(),
          }),
        );
      }

      switch (data.type) {
        case 'notification':
          notificationStore.handleNewNotification(data.notification);
          break;
        case 'heartbeat_ack':
          handleHeartbeatResponse();
          break;
        case 'error':
          console.error('服务器错误:', data.message);
          break;
        default:
          console.log('收到未知类型的消息:', data);
      }
    } catch (error) {
      console.error('解析 WebSocket 消息失败:', error);
    }
  };

  // 优化的心跳处理
  let currentHeartbeatInterval = HEARTBEAT_CONFIG.initialDelay;
  let heartbeatTimeoutId: number | null = null;
  let missedHeartbeats = 0;

  const handleHeartbeatResponse = () => {
    missedHeartbeats = 0;
    lastHeartbeatResponse.value = Date.now();
    // 如果连接稳定，逐渐增加心跳间隔
    if (missedHeartbeats === 0) {
      currentHeartbeatInterval = calculateNextHeartbeatInterval(currentHeartbeatInterval);
    }
  };

  const startHeartbeat = () => {
    if (heartbeatTimeoutId) {
      clearTimeout(heartbeatTimeoutId);
    }

    const sendHeartbeat = () => {
      if (ws.value?.readyState === WebSocket.OPEN) {
        missedHeartbeats++;

        // 如果连续多次未收到响应，缩短心跳间隔
        if (missedHeartbeats > 1) {
          currentHeartbeatInterval = Math.max(
            currentHeartbeatInterval / 2,
            HEARTBEAT_CONFIG.initialDelay,
          );
        }

        // 如果超过最大未响应次数，重新连接
        if (missedHeartbeats > 3) {
          console.warn('多次心跳未响应，重新连接');
          ws.value.close();
          return;
        }

        ws.value.send(
          JSON.stringify({
            type: 'heartbeat',
            timestamp: Date.now(),
          }),
        );

        heartbeatTimeoutId = window.setTimeout(sendHeartbeat, currentHeartbeatInterval);
      }
    };

    heartbeatTimeoutId = window.setTimeout(sendHeartbeat, currentHeartbeatInterval);
  };

  const connect = () => {
    if (ws.value?.readyState === WebSocket.OPEN || forceClosed.value) {
      return;
    }

    if (isReconnecting.value) {
      return;
    }

    isReconnecting.value = true;
    clearTimeouts();

    try {
      const wsUrl = `${import.meta.env.VITE_WS_URL}/notifications/`;
      ws.value = new WebSocket(wsUrl);

      connectionTimeoutId.value = window.setTimeout(() => {
        if (ws.value?.readyState !== WebSocket.OPEN) {
          console.error('WebSocket 连接超时');
          ws.value?.close();
        }
      }, connectionTimeout);

      ws.value.onopen = () => {
        console.log('WebSocket 已连接');
        isConnected.value = true;
        notificationStore.setWebSocketConnected(true);
        reconnectAttempts.value = 0;
        isReconnecting.value = false;
        clearTimeouts();
        startHeartbeat();
        startKeepAlive();

        const userId = localStorage.getItem('userId');
        if (userId) {
          subscribe({ userId });
        }

        processMessageQueue();
      };

      ws.value.onclose = event => {
        console.log(`WebSocket 已断开 (code: ${event.code}, reason: ${event.reason})`);
        isConnected.value = false;
        isReconnecting.value = false;
        notificationStore.setWebSocketConnected(false);
        clearTimeouts();
        stopKeepAlive();

        if (!forceClosed.value && reconnectAttempts.value < maxReconnectAttempts) {
          reconnectAttempts.value++;
          const delay = calculateReconnectDelay();
          console.log(`将在 ${delay}ms 后尝试重新连接 (第 ${reconnectAttempts.value} 次)`);
          reconnectTimeout.value = window.setTimeout(connect, delay);
        } else if (reconnectAttempts.value >= maxReconnectAttempts) {
          console.error('WebSocket 重连次数超过限制，停止重连');
        }
      };

      ws.value.onerror = error => {
        console.error('WebSocket 错误:', error);
      };

      ws.value.onmessage = handleMessage;
    } catch (error) {
      console.error('创建 WebSocket 连接失败:', error);
      isReconnecting.value = false;
    }
  };

  const disconnect = (force: boolean = false) => {
    forceClosed.value = force;
    clearTimeouts();
    stopKeepAlive();

    if (ws.value) {
      ws.value.close();
      ws.value = null;
    }
  };

  const subscribe = (options: { userId: string; modules?: string[] }) => {
    send(
      {
        type: 'subscribe',
        ...options,
      },
      10,
    ); // 订阅消息使用高优先级
  };

  const stopHeartbeat = () => {
    if (heartbeatTimeoutId) {
      clearTimeout(heartbeatTimeoutId);
      heartbeatTimeoutId = null;
    }
  };

  const clearTimeouts = () => {
    if (reconnectTimeout.value) {
      clearTimeout(reconnectTimeout.value);
      reconnectTimeout.value = null;
    }
    if (connectionTimeoutId.value) {
      clearTimeout(connectionTimeoutId.value);
      connectionTimeoutId.value = null;
    }
    stopHeartbeat();
  };

  const calculateReconnectDelay = () => {
    const delay =
      initialReconnectDelay * Math.pow(reconnectBackoffMultiplier, reconnectAttempts.value);
    return Math.min(delay, maxReconnectDelay);
  };

  onMounted(() => {
    connect();
  });

  onUnmounted(() => {
    disconnect(true);
  });

  return {
    isConnected,
    connect,
    disconnect,
    send,
    subscribe,
  };
};
