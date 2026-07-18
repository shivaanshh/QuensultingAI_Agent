import type {
  Analytics,
  Booking,
  BookingStatus,
  CallEvent,
  Category,
  ContactRequest,
  ContactResponse,
  ProvisionResult,
  Service,
  ServiceCreate,
  ServiceUpdate,
  TenantCreateRequest,
  TenantDetail,
  TenantListItem,
  TenantSettingsUpdate,
} from './types'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      if (typeof body?.detail === 'string') detail = body.detail
    } catch {
      // response wasn't JSON -- fall back to statusText
    }
    throw new ApiError(res.status, detail)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  getCategories: () => request<Category[]>('/api/categories'),
  listTenants: () => request<TenantListItem[]>('/api/tenants'),
  getTenant: (slug: string) => request<TenantDetail>(`/api/tenants/${encodeURIComponent(slug)}`),
  createTenant: (body: TenantCreateRequest) =>
    request<TenantDetail>('/api/tenants', { method: 'POST', body: JSON.stringify(body) }),
  previewTenant: (slug: string) =>
    request<Record<string, unknown>>(`/api/tenants/${encodeURIComponent(slug)}/preview`),
  provisionTenant: (slug: string, reprovision = false) =>
    request<ProvisionResult>(
      `/api/tenants/${encodeURIComponent(slug)}/provision?reprovision=${reprovision}`,
      { method: 'POST' }
    ),
  submitContact: (body: ContactRequest) =>
    request<ContactResponse>('/api/contact', { method: 'POST', body: JSON.stringify(body) }),

  // ── business-owner portal ──
  listCalls: (slug: string, limit = 50) =>
    request<CallEvent[]>(`/api/tenants/${encodeURIComponent(slug)}/calls?limit=${limit}`),
  getAnalytics: (slug: string, days = 30) =>
    request<Analytics>(`/api/tenants/${encodeURIComponent(slug)}/analytics?days=${days}`),
  updateBookingStatus: (slug: string, bookingId: number, status: BookingStatus) =>
    request<Booking>(`/api/tenants/${encodeURIComponent(slug)}/bookings/${bookingId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),
  listServices: (slug: string) =>
    request<Service[]>(`/api/tenants/${encodeURIComponent(slug)}/services`),
  addService: (slug: string, body: ServiceCreate) =>
    request<Service>(`/api/tenants/${encodeURIComponent(slug)}/services`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  updateService: (slug: string, serviceId: number, body: ServiceUpdate) =>
    request<Service>(`/api/tenants/${encodeURIComponent(slug)}/services/${serviceId}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  deleteService: (slug: string, serviceId: number) =>
    request<void>(`/api/tenants/${encodeURIComponent(slug)}/services/${serviceId}`, {
      method: 'DELETE',
    }),
  updateSettings: (slug: string, body: TenantSettingsUpdate) =>
    request<TenantDetail>(`/api/tenants/${encodeURIComponent(slug)}/settings`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
}
