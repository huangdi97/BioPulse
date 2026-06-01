import { useEffect, useRef, useState } from 'react'
import { scanContent } from '@/api/compliance'
import type { ScanResult } from '@/types'

interface ComplianceScannerProps {
  content: string
  onResult: (result: ScanResult) => void
}

export default function ComplianceScanner({ content, onResult }: ComplianceScannerProps) {
  const [status, setStatus] = useState<'idle' | 'scanning'>('idle')
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const onResultRef = useRef(onResult)
  onResultRef.current = onResult

  useEffect(() => {
    if (!content.trim()) {
      setStatus('idle')
      onResultRef.current({
        passed: true,
        riskLevel: 'low',
        violations: [],
        score: 100,
      })
      return
    }

    if (timerRef.current) {
      clearTimeout(timerRef.current)
    }

    setStatus('idle')

    timerRef.current = setTimeout(async () => {
      setStatus('scanning')
      const result = await scanContent(content)
      onResultRef.current(result)
      setStatus('idle')
    }, 500)

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
    }
  }, [content])

  return null
}

export type { ComplianceScannerProps }
