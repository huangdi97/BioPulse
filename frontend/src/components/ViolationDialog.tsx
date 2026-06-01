import type { Violation } from '@/types'
import { Button } from '@/components/ui/button'
import { AlertTriangle, X } from 'lucide-react'

interface ViolationDialogProps {
  open: boolean
  violations: Violation[]
  onModify: () => void
  onForceSubmit: () => void
}

const riskBadgeStyle: Record<string, string> = {
  critical: 'bg-red-100 text-red-700 border-red-300',
  high: 'bg-orange-100 text-orange-700 border-orange-300',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-300',
  low: 'bg-blue-100 text-blue-700 border-blue-300',
}

const categoryBadgeStyle: Record<string, string> = {
  '虚假宣传': 'bg-red-50 text-red-600',
  '违规宣称': 'bg-orange-50 text-orange-600',
  '不正当竞争': 'bg-yellow-50 text-yellow-600',
  '夸大宣传': 'bg-orange-50 text-orange-600',
}

export default function ViolationDialog({
  open,
  violations,
  onModify,
  onForceSubmit,
}: ViolationDialogProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onModify} />

      <div className="relative z-10 w-[90vw] max-w-md rounded-xl bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <h3 className="text-base font-semibold text-gray-900">
              内容合规风险提示
            </h3>
          </div>
          <button
            onClick={onModify}
            className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="max-h-[50vh] overflow-y-auto px-5 py-4">
          <p className="mb-4 text-sm text-gray-600">
            检测到 {violations.length} 项合规风险，请修改后重新提交：
          </p>

          <div className="space-y-3">
            {violations.map((v, idx) => (
              <div
                key={idx}
                className="rounded-lg border border-gray-200 bg-gray-50 p-3"
              >
                <div className="mb-2 flex items-center gap-2">
                  <span
                    className={`rounded border px-2 py-0.5 text-xs font-medium ${riskBadgeStyle[v.riskLevel] ?? 'bg-gray-100 text-gray-600 border-gray-300'}`}
                  >
                    {v.riskLevel === 'critical'
                      ? '严重'
                      : v.riskLevel === 'high'
                        ? '高风险'
                        : v.riskLevel === 'medium'
                          ? '中风险'
                          : '低风险'}
                  </span>
                  <span
                    className={`rounded px-2 py-0.5 text-xs font-medium ${categoryBadgeStyle[v.category] ?? 'bg-gray-50 text-gray-600'}`}
                  >
                    {v.category}
                  </span>
                </div>

                <p className="text-sm">
                  <span className="font-medium">违规词：</span>
                  <span className="rounded bg-red-100 px-1.5 py-0.5 text-xs font-mono text-red-700">
                    {v.keyword}
                  </span>
                </p>

                {v.suggestion && (
                  <p className="mt-1 text-sm">
                    <span className="font-medium">修改建议：</span>
                    <span className="text-gray-700">{v.suggestion}</span>
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="flex gap-3 border-t px-5 py-4">
          <Button
            variant="destructive"
            onClick={onForceSubmit}
            className="flex-1"
          >
            强制提交
          </Button>
          <Button onClick={onModify} className="flex-1">
            修改内容
          </Button>
        </div>
      </div>
    </div>
  )
}

export type { ViolationDialogProps }
