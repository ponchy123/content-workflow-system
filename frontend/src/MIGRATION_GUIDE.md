# 前端代码迁移指南

## HTTP请求工具迁移

### 背景

项目中曾经同时存在两个HTTP请求工具模块：
- `utils/request.ts`：简单的Axios封装
- `api/core/request.ts`：功能完整的HTTP客户端实现

为了减少代码重复和统一HTTP请求处理逻辑，我们已经删除了 `utils/request.ts` 并将所有引用迁移到了 `api/core/request.ts`。

### 迁移步骤

如果你有任何代码仍然引用 `utils/request.ts`，请按照以下步骤迁移：

#### 1. 替换导入语句

| 旧导入 | 新导入 |
|-------|-------|
| `import { request } from '@/utils/request'` | `import { httpService as request } from '@/api/core/request'` |
| `import { validateResponse, retryRequest } from '@/utils/request'` | `import { validateResponse, retryRequest } from '@/api/core/request'` |
| `import request from '@/utils/request'` | `import { httpService as request } from '@/api/core/request'` |

#### 2. 更新API用法（如需要）

`api/core/request.ts`提供了更多高级功能，可以根据需要使用：

```typescript
// 基本使用
const data = await request.get('/api/users');

// 带缓存的请求
const data = await request.get('/api/users', { shouldCache: true, cacheTTL: 60000 });

// 带优先级的请求
const data = await request.post('/api/important', payload, { priority: 1 });

// 防抖请求
const data = await request.debouncedRequest({ url: '/api/search', method: 'GET', params: { q: keyword } });

// 节流请求
const data = await request.throttledRequest({ url: '/api/search', method: 'GET', params: { q: keyword } });
```

#### 3. 已迁移的文件

以下文件已经完成了迁移：
- `frontend/src/stores/product.ts`
- `frontend/src/composables/useProductComparison.ts`
- `frontend/src/api/notifications/notification.ts`

### 优势

使用`api/core/request.ts`的优势：

1. **更丰富的功能**：提供请求队列管理、缓存、防抖、节流等高级功能
2. **性能监控**：内置性能监控和错误报告
3. **更好的类型支持**：完整的TypeScript类型定义
4. **离线支持**：结合Service Worker提供离线功能
5. **安全增强**：内置CSRF保护和敏感数据加密

### 注意事项

1. 由于`utils/request.ts`已被删除，所有引用它的代码将无法编译，需要立即更新
2. 如果你在迁移过程中遇到问题，请查看`api/core/request.ts`文件中的可用功能和类型定义
3. 所有新开发的功能应直接使用`api/core/request.ts` 