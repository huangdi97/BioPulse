import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { TaskFormData } from '@/types/inspection'

interface InspectionTaskModalProps {
  open: boolean
  onClose: () => void
  onSubmit: (data: TaskFormData) => void
  title?: string
  defaultReps?: string[]
}

export default function InspectionTaskModal({ open, onClose, onSubmit, title, defaultReps }: InspectionTaskModalProps) {
  const [form, setForm] = useState<TaskFormData>({ title: '', description: '', assignee: '', deadline: '' })

  if (!open) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <Card className="w-full max-w-lg mx-4" onClick={e => e.stopPropagation()}>
        <CardHeader>
          <CardTitle className="text-base">{title || '创建整改任务'}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-1">
            <Label className="text-xs">任务标题</Label>
            <Input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="输入标题" />
          </div>
          <div className="space-y-1">
            <Label className="text-xs">描述</Label>
            <Input value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="可选" />
          </div>
          <div className="space-y-1">
            <Label className="text-xs">负责人</Label>
            {defaultReps && defaultReps.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-2">
                {defaultReps.map(name => (
                  <button
                    key={name}
                    onClick={() => setForm(f => ({ ...f, assignee: name }))}
                    className={`px-2 py-1 text-xs rounded border transition-colors ${
                      form.assignee === name ? 'bg-primary text-primary-foreground border-primary' : 'bg-background hover:bg-muted'
                    }`}
                  >
                    {name}
                  </button>
                ))}
              </div>
            )}
            <Input value={form.assignee} onChange={e => setForm(f => ({ ...f, assignee: e.target.value }))} placeholder="输入姓名" />
          </div>
          <div className="space-y-1">
            <Label className="text-xs">截止日期</Label>
            <Input type="date" value={form.deadline} onChange={e => setForm(f => ({ ...f, deadline: e.target.value }))} />
          </div>
          <div className="flex gap-2 justify-end pt-2">
            <Button variant="outline" onClick={onClose}>取消</Button>
            <Button onClick={() => onSubmit(form)} disabled={!form.title || !form.assignee || !form.deadline}>创建</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
