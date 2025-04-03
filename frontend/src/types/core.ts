// 服务商类型定义
export interface ServiceProvider {
  id: number
  name: string
  code: string
  contact_person?: string
  contact_phone?: string
  contact_email?: string
  status: boolean
  api_key?: string
  api_secret?: string
  config?: Record<string, any>
  created_at: string
  updated_at: string
} 