export interface ServiceDefault {
  name: string
  price_display: string
  duration_minutes: number | null
}

export interface Category {
  key: string
  display_name: string
  agent_persona_name: string
  booking_noun: string
  customer_noun: string
  default_services: ServiceDefault[]
  fact_bullet_labels: [string, string][]
  extra_slots: Record<string, unknown>[]
}

export interface TenantListItem {
  id: number
  slug: string
  category: string
  business_name: string
  status: string
  created_at: string
  provisioned: boolean
}

export interface Service {
  id: number
  name: string
  price_display: string
  duration_minutes: number | null
  sort_order: number
  is_active: boolean
}

export interface Booking {
  id: number
  booking_reference: string
  service_name_snapshot: string
  customer_name: string
  phone_number: string
  email: string
  confirmed_datetime: string
  status: string
  created_at: string
  extra_fields: Record<string, unknown>
}

export interface TenantDetail {
  id: number
  slug: string
  category: string
  business_name: string
  timezone: string
  open_hour: number
  close_hour: number
  open_weekdays: number[]
  address: string
  transfer_number: string
  booking_reference_prefix: string
  notification_email: string
  google_sheets_id: string
  retell_voice_id: string
  retell_conversation_flow_id: string
  retell_agent_id: string
  status: string
  created_at: string
  services: Service[]
  bookings: Booking[]
}

export interface TenantCreateRequest {
  slug: string
  category: string
  business_name: string
  timezone?: string
  open_hour?: number
  close_hour?: number
  open_weekdays?: number[]
  address?: string
  transfer_number?: string
  booking_reference_prefix?: string | null
  notification_email?: string
  google_sheets_id?: string
  services?: string[]
}

export interface ProvisionResult {
  conversation_flow_id: string
  agent_id: string
}

export interface ContactRequest {
  name: string
  email: string
  business_type?: string
  message: string
}

export interface ContactResponse {
  status: string
  message: string
}

export interface CallEvent {
  id: number
  call_id: string
  direction: string
  from_number: string
  to_number: string
  call_status: string
  duration_seconds: number | null
  disconnection_reason: string
  user_sentiment: string
  call_successful: boolean | null
  summary: string
  transcript: string
  booking_reference: string
  started_at: string | null
  ended_at: string | null
  created_at: string
}

export interface SeriesPoint {
  date: string
  calls: number
  bookings: number
}

export interface LabelCount {
  label: string
  count: number
}

export interface Analytics {
  days: number
  total_calls: number
  total_bookings: number
  total_call_minutes: number
  avg_call_seconds: number
  answered_calls: number
  booking_conversion: number
  provisioned: boolean
  series: SeriesPoint[]
  sentiment: LabelCount[]
  top_services: LabelCount[]
}

export type BookingStatus = 'confirmed' | 'completed' | 'cancelled' | 'no_show'

export interface ServiceCreate {
  name: string
  price_display?: string
  duration_minutes?: number | null
  description?: string
}

export interface ServiceUpdate {
  name?: string
  price_display?: string
  duration_minutes?: number | null
  description?: string
  is_active?: boolean
  sort_order?: number
}

export interface TenantSettingsUpdate {
  business_name?: string
  timezone?: string
  open_hour?: number
  close_hour?: number
  open_weekdays?: number[]
  address?: string
  transfer_number?: string
  notification_email?: string
  status?: string
}
