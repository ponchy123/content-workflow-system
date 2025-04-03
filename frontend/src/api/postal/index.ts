// 导出邮政编码管理相关的API函数
export {
  getPostalCodes,
  getAddressByPostalCode,
  searchPostalCode,
  // 邮编分区相关函数
  getZipZones,
  getZipZone,
  createZipZone,
  updateZipZone,
  deleteZipZone,
  // 偏远地区相关函数
  getRemoteAreas,
  getRemoteArea,
  createRemoteArea,
  updateRemoteArea,
  deleteRemoteArea,
  // 检查函数
  checkZipZoneExists,
  checkRemoteAreaExists,
  // 查询分区
  queryZoneByZip,
  // 导入函数
  importZipZones,
} from './postal';

// 导出类型定义
export type {
  PostalCode,
  PostalSearchResult,
  ZipZone,
  ZipZoneCreateRequest,
  ZipZoneUpdateRequest,
  ZipZoneListParams,
  RemoteArea,
  RemoteAreaCreateRequest,
  RemoteAreaUpdateRequest,
  RemoteAreaListParams,
} from './postal';
