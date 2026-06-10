import { useEffect, useRef, useState, useCallback } from 'react'

export interface StreamEvent {
  event: string
  data: Record<string, unknown>
  timestamp: string
}

interface UseAgentStreamResult {
  events: StreamEvent[]
  isConnected: boolean
  error: string | null
  connect: (traceId: string) => void
  disconnect: () => void
}

export function useAgentStream(): UseAgentStreamResult {
  const [events, setEvents] = useState<StreamEvent[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  const connect = useCallback((traceId: string) => {
    disconnect()
    setEvents([])
    setError(null)
    const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
    const url = `${baseUrl}/agent/traces/${traceId}/stream`
    const es = new EventSource(url)
    eventSourceRef.current = es

    es.onopen = () => {
      setIsConnected(true)
      setError(null)
    }

    es.addEventListener('agent.start', (e) => {
      try {
        const data = JSON.parse(e.data)
        setEvents((prev) => [...prev, { event: 'agent.start', data, timestamp: new Date().toISOString() }])
      } catch { /* ignore parse errors */ }
    })

    es.addEventListener('agent.tool_call', (e) => {
      try {
        const data = JSON.parse(e.data)
        setEvents((prev) => [...prev, { event: 'agent.tool_call', data, timestamp: new Date().toISOString() }])
      } catch { /* ignore parse errors */ }
    })

    es.addEventListener('agent.tool_result', (e) => {
      try {
        const data = JSON.parse(e.data)
        setEvents((prev) => [...prev, { event: 'agent.tool_result', data, timestamp: new Date().toISOString() }])
      } catch { /* ignore parse errors */ }
    })

    es.addEventListener('agent.llm_call', (e) => {
      try {
        const data = JSON.parse(e.data)
        setEvents((prev) => [...prev, { event: 'agent.llm_call', data, timestamp: new Date().toISOString() }])
      } catch { /* ignore parse errors */ }
    })

    es.addEventListener('agent.llm_result', (e) => {
      try {
        const data = JSON.parse(e.data)
        setEvents((prev) => [...prev, { event: 'agent.llm_result', data, timestamp: new Date().toISOString() }])
      } catch { /* ignore parse errors */ }
    })

    es.addEventListener('agent.end', (e) => {
      try {
        const data = JSON.parse(e.data)
        setEvents((prev) => [...prev, { event: 'agent.end', data, timestamp: new Date().toISOString() }])
      } catch { /* ignore parse errors */ }
    })

    es.addEventListener('agent.error', (e) => {
      try {
        const data = JSON.parse(e.data)
        setEvents((prev) => [...prev, { event: 'agent.error', data, timestamp: new Date().toISOString() }])
      } catch { /* ignore parse errors */ }
    })

    es.onerror = () => {
      setIsConnected(false)
      setError('SSE connection failed')
      es.close()
      eventSourceRef.current = null
    }
  }, [])

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setIsConnected(false)
  }, [])

  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return { events, isConnected, error, connect, disconnect }
}
