import axios from 'axios'

export const END_PORTS: Record<string, number> = {
  cloud: Number(import.meta.env.VITE_CLOUD_PORT) || 8000,
  coach: Number(import.meta.env.VITE_COACH_PORT) || 8001,
  opportunity: Number(import.meta.env.VITE_OPPORTUNITY_PORT) || 8002,
  assistant: Number(import.meta.env.VITE_ASSISTANT_PORT) || 8003,
  sales_assistant: Number(import.meta.env.VITE_SALES_ASSISTANT_PORT) || 8004,
}

export function getApiUrl(end: string, path: string): string {
  if (import.meta.env.DEV) {
    return `/api/${end === 'coach' ? 'sales-coach' : end === 'sales_assistant' ? 'sales-assistant' : end}${path}`
  }
  const base = import.meta.env.VITE_API_GATEWAY || 'http://localhost:8000'
  return `${base}${path}`
}

export async function withFallback<T>(fn: () => Promise<T>, fallback: () => T): Promise<T> {
  try {
    return await fn()
  } catch (err) {
    if (import.meta.env.DEV) {
      return fallback()
    }
    throw err
  }
}

const client = axios.create({
  baseURL: '',
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => {
    if (response.data && typeof response.data.code === 'number' && 'data' in response.data) {
      response.data = response.data.data
    }
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default client
