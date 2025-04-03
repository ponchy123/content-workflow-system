// 请确认这是否符合实际后端API路径
export default {
  // 产品相关接口
  products: '/api/v1/products/products/',
  publicProducts: '/api/v1/products/products/public_product_list/',
  productDetail: (id: string) => `/api/v1/products/products/${id}/`,
  uploadProductExcel: '/api/v1/products/products/upload_product_excel/',
  downloadProductTemplate: '/api/v1/products/products/download_product_template/',
  downloadProductTemplateWithData: '/api/v1/products/products/download_product_template_with_data/',
  
  // 检查产品数据完整性
  checkProductIntegrity: (id: string) => `/api/v1/products/products/${id}/check_integrity/`,
  batchCheckIntegrity: '/api/v1/products/batch_check_integrity/',
  
  // 重量段接口
  weightBands: '/api/v1/products/weight_bands/',
  weightBand: (id: string) => `/api/v1/products/weight_bands/${id}/`,
  weightBandsByProduct: (productId: string) => `/api/v1/products/products/${productId}/weight_bands/`,
  
  // 区域费率接口 - 已废弃，请使用基础费率接口（BaseFee）
  // @deprecated 请使用 baseFees API 替代
  zoneRates: '/api/v1/products/zone_rates/',
  zoneRate: (id: string) => `/api/v1/products/zone_rates/${id}/`,
  zoneRatesByProduct: (productId: string) => `/api/v1/products/products/${productId}/zone_rates/`,
  
  // 基础费率接口 - 包含区域价格信息
  baseFees: '/api/v1/products/base-fees/',
  baseFee: (id: string) => `/api/v1/products/base-fees/${id}/`,
  baseFeesByProduct: (productId: string) => `/api/v1/products/products/${productId}/base-fees/`,
  
  // 附加费接口
  surcharges: '/api/v1/products/surcharges/',
  surcharge: (id: string) => `/api/v1/products/surcharges/${id}/`,
  surchargesByProduct: (productId: string) => `/api/v1/products/products/${productId}/surcharges/`,
  
  // 旺季附加费接口
  peakSeasonSurcharges: '/api/v1/products/peak_season_surcharges/',
  peakSeasonSurcharge: (id: string) => `/api/v1/products/peak_season_surcharges/${id}/`,
  peakSeasonSurchargesByProduct: (productId: string) => `/api/v1/products/products/${productId}/peak_season_surcharges/`,
  
  // 增值服务接口 - 删除或替换为新的API端点
  // valueAddedServices: '/api/v1/products/special_rules/',
  // valueAddedService: (id: string) => `/api/v1/products/special_rules/${id}/`,
  // valueAddedServicesByProduct: (productId: string) => `/api/v1/products/products/${productId}/special_rules/`,
  
  // 产品导入/导出接口
  importProducts: '/api/v1/products/import_products/',
  exportProducts: '/api/v1/products/export_products/',
  
  // 服务商接口
  serviceProviders: '/api/v1/core/service_providers/',
  serviceProvider: (id: string) => `/api/v1/core/service_providers/${id}/`,
}; 