import axios from 'axios'

export const END_PORTS: Record<string, number> = {
  cloud: 8000,
  coach: 8001,
  opportunity: 8002,
  assistant: 8003,
  sales_assistant: 8004,
}

export function getApiUrl(end: string, path: string): string {
  const port = END_PORTS[end] ?? 8000
  if (import.meta.env.DEV) {
    return `/api/${end === 'coach' ? 'sales-coach' : end === 'sales_assistant' ? 'sales-assistant' : end}${path}`
  }
  return `http://localhost:${port}${path}`
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
