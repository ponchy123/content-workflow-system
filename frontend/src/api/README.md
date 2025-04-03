# API Documentation

## Core Module
The core module provides basic HTTP request utilities and common types.

### Types
- `ApiResponse<T>`: Generic type for API responses
- `PaginatedResponse<T>`: Generic type for paginated responses

## Calculator Module
Handles freight calculation related operations.

### Functions
- `calculate(data: CalculationRequest): Promise<CalculationResponse>`
  - Calculates freight cost for a single shipment
  - Parameters: origin, destination, weight, dimensions, etc.

- `calculateBatch(data: BatchCalculationRequest): Promise<BatchCalculationResponse>`
  - Processes multiple freight calculations in batch
  - Returns a task ID for status tracking

- `getBatchTaskStatus(taskId: string): Promise<BatchCalculationResponse>`
  - Checks the status of a batch calculation task
  - Returns progress and results if available

- `compareProducts(data: ComparisonRequest): Promise<ComparisonResponse>`
  - Compares shipping costs across different products
  - Useful for finding the most cost-effective option

- `saveCalculationResult(data: CalculationRequest): Promise<void>`
  - Saves calculation results for future reference

## Products Module
Manages product-related operations including rules, weight ranges, and zone prices.

### Base Product Operations
- `getProductList(params?: ProductListParams): Promise<ProductListResponse>`
- `getProductDetail(id: string): Promise<Product>`
- `createProduct(data: ProductCreateRequest): Promise<Product>`
- `updateProduct(id: string, data: ProductUpdateRequest): Promise<Product>`
- `deleteProduct(id: string): Promise<void>`

### Weight Range Operations
- `getWeightRangeList(productId: string, params?): Promise<WeightRangeListResponse>`
- `getWeightRangeDetail(productId: string, id: string): Promise<WeightRange>`
- `createWeightRange(productId: string, data: WeightRangeCreateRequest): Promise<WeightRange>`
- `updateWeightRange(productId: string, id: string, data: WeightRangeUpdateRequest): Promise<WeightRange>`
- `deleteWeightRange(productId: string, id: string): Promise<void>`

### Zone Price Operations
- `getZonePriceList(productId: string, weightRangeId: string, params?): Promise<ZonePriceListResponse>`
- `getZonePriceDetail(productId: string, weightRangeId: string, id: string): Promise<ZonePrice>`
- `createZonePrice(productId: string, weightRangeId: string, data: ZonePriceCreateRequest): Promise<ZonePrice>`
- `updateZonePrice(productId: string, weightRangeId: string, id: string, data: ZonePriceUpdateRequest): Promise<ZonePrice>`
- `deleteZonePrice(productId: string, weightRangeId: string, id: string): Promise<void>`

### Special Rule Operations
- `getSpecialRuleList(productId: string, params?): Promise<SpecialRuleListResponse>`
- `getSpecialRuleDetail(productId: string, id: string): Promise<SpecialRule>`
- `createSpecialRule(productId: string, data: SpecialRuleCreateRequest): Promise<SpecialRule>`
- `updateSpecialRule(productId: string, id: string, data: SpecialRuleUpdateRequest): Promise<SpecialRule>`
- `deleteSpecialRule(productId: string, id: string): Promise<void>`

## Notifications Module
Handles system notifications and user alerts.

### Functions
- `getNotificationList(params?: NotificationListParams): Promise<NotificationListResponse>`
- `getNotificationDetail(id: string): Promise<Notification>`
- `createNotification(data: NotificationCreateRequest): Promise<Notification>`
- `updateNotification(id: string, data: NotificationUpdateRequest): Promise<Notification>`
- `deleteNotification(id: string): Promise<void>`
- `markNotificationAsRead(id: string): Promise<void>`
- `markAllNotificationsAsRead(): Promise<void>`
- `clearReadNotifications(): Promise<void>`

## Usage Example
```typescript
import { calculateBatch, getBatchTaskStatus } from '@/api/calculator';
import type { BatchCalculationRequest } from '@/types/calculator';

async function processBatchCalculation(data: BatchCalculationRequest) {
  try {
    // Start batch calculation
    const response = await calculateBatch(data);
    const taskId = response.task_id;

    // Poll for results
    const result = await getBatchTaskStatus(taskId);
    return result;
  } catch (error) {
    console.error('Batch calculation failed:', error);
    throw error;
  }
} 