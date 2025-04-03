import type { ServiceProvider } from './core';

export interface PostalCode {
  postal_code: string;
}

// 邮编搜索结果接口
export interface PostalSearchResult {
  postal_code: string;
}

export interface ZipZone {
  id: number;
  provider_id: number;
  provider?: ServiceProvider;
  origin_zip: string;
  dest_zip_start: string;
  dest_zip_end: string;
  zone_number: number;
  created_at: string;
  updated_at: string;
  created_by: string;
  updated_by: string;
  is_deleted: boolean;
}

export interface ZipZoneCreateRequest {
  provider_id: number;
  origin_zip: string;
  dest_zip_start: string;
  dest_zip_end: string;
  zone_number: number;
}

export interface ZipZoneUpdateRequest {
  provider_id?: number;
  origin_zip?: string;
  dest_zip_start?: string;
  dest_zip_end?: string;
  zone_number?: number;
}

export interface ZipZoneListParams {
  page: number;
  page_size: number;
  provider_id?: number;
  origin_zip?: string;
  zone_number?: number;
  dest_zip?: string;
}

export interface RemoteArea {
  id: number;
  provider_id: number;
  provider?: ServiceProvider;
  origin_zip: string;
  zip_code: string;
  remote_level: string;
  created_at: string;
  updated_at: string;
  created_by: string;
  updated_by: string;
  is_deleted: boolean;
}

export interface RemoteAreaCreateRequest {
  provider_id: number;
  origin_zip: string;
  zip_code: string;
  remote_level: string;
}

export interface RemoteAreaUpdateRequest {
  provider_id?: number;
  origin_zip?: string;
  zip_code?: string;
  remote_level?: string;
}

export interface RemoteAreaListParams {
  page: number;
  page_size: number;
  provider_id?: number;
  origin_zip?: string;
  remote_level?: string;
  zip_code?: string;
} 