import { useEffect, useRef } from 'react'
import { scanContent } from '@/api/compliance'
import type { ScanResult } from '@/types'

interface ComplianceScannerProps {
  content: string
  onResult: (result: ScanResult) => void
}

export default function ComplianceScanner({ content, onResult }: ComplianceScannerProps) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const onResultRef = useRef(onResult)
  onResultRef.current = onResult

  useEffect(() => {
    if (!content.trim()) {
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

    timerRef.current = setTimeout(async () => {
      const result = await scanContent(content)
      onResultRef.current(result)
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
