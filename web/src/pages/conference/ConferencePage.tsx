import { useState } from "react"
import { Card, CardContent } from "../../components/ui/Card"
import { Button } from "../../components/ui/Button"
import { Input } from "../../components/ui/Input"
import {
  createConference,
  inviteConference,
  checkinConference,
  getConferenceAnalytics,
} from "../../api/client"

const MEETING_TYPES = [
  { value: 'webinar', label: '网络研讨会' },
  { value: 'satellite', label: '卫星会' },
]

export default function ConferencePage() {
  const [view, setView] = useState<'create' | 'checkin' | 'analytics'>('create')
  const [confId, setConfId] = useState('')
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({ title: '', type: 'webinar', date: '', duration: 60, speaker: '' })
  const [createdId, setCreatedId] = useState<string | null>(null)

  const [checkinHcpId, setCheckinHcpId] = useState('')
  const [checkinResult, setCheckinResult] = useState<any>(null)
  const [inviteResult, setInviteResult] = useState<any>(null)

  const [analyticsData, setAnalyticsData] = useState<any>(null)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)
  const [analyticsId, setAnalyticsId] = useState('')

  async function handleCreate() {
    setCreating(true)
    const data = await createConference({
      title: form.title || '未命名会议',
      type: form.type,
      date: form.date || new Date().toISOString().slice(0, 16),
      duration: form.duration || 60,
      speaker: form.speaker || undefined,
    })
    if (data) {
      setCreatedId(data.id)
      setConfId(data.id)
    }
    setCreating(false)
  }

  async function handleInvite() {
    if (!confId) return
    const data = await inviteConference(confId, ['hcp-001', 'hcp-002', 'hcp-003'])
    setInviteResult(data)
  }

  async function handleCheckin() {
    if (!confId || !checkinHcpId) return
    const data = await checkinConference(confId, checkinHcpId)
    setCheckinResult(data)
  }

  async function handleAnalytics() {
    const id = analyticsId || confId
    if (!id) return
    setAnalyticsLoading(true)
    const data = await getConferenceAnalytics(id)
    setAnalyticsData(data)
    setAnalyticsLoading(false)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--clr-text-primary)' }}>学术会议</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--clr-text-secondary)' }}>创建、签到与数据分析</p>
      </div>

      <div className="flex gap-1 p-1 rounded-lg w-fit" style={{ backgroundColor: 'var(--clr-gray-10)' }}>
        {([['create', '创建会议'], ['checkin', '签到管理'], ['analytics', '会议分析']] as const).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setView(key)}
            className={`px-4 py-1.5 text-sm rounded-md transition-colors ${
              view === key ? 'bg-white shadow-sm font-medium' : ''
            }`}
            style={{ color: view === key ? 'var(--clr-text-primary)' : 'var(--clr-text-secondary)' }}
          >
            {label}
          </button>
        ))}
      </div>

      {view === 'create' && (
        <div className="space-y-4 max-w-lg">
          <Card>
            <CardContent className="p-4 space-y-3">
              <h3 className="text-sm font-semibold" style={{ color: 'var(--clr-text-primary)' }}>创建会议</h3>

              <div className="space-y-1">
                <label className="text-xs font-medium" style={{ color: 'var(--clr-text-secondary)' }}>会议名称</label>
                <Input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="输入会议名称" />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium" style={{ color: 'var(--clr-text-secondary)' }}>会议类型</label>
                <select
                  value={form.type}
                  onChange={e => setForm(f => ({ ...f, type: e.target.value }))}
                  className="h-9 rounded-md border px-3 text-sm bg-white w-full"
                  style={{ borderColor: 'var(--clr-border-default)', color: 'var(--clr-text-primary)' }}
                >
                  {MEETING_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium" style={{ color: 'var(--clr-text-secondary)' }}>会议时间</label>
                <Input type="datetime-local" value={form.date} onChange={e => setForm(f => ({ ...f, date: e.target.value }))} />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium" style={{ color: 'var(--clr-text-secondary)' }}>时长(分钟)</label>
                <Input type="number" value={form.duration} onChange={e => setForm(f => ({ ...f, duration: Number(e.target.value) }))} min={15} max={240} />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium" style={{ color: 'var(--clr-text-secondary)' }}>讲者</label>
                <Input value={form.speaker} onChange={e => setForm(f => ({ ...f, speaker: e.target.value }))} placeholder="可选" />
              </div>

              <Button onClick={handleCreate} disabled={creating} className="w-full">
                {creating ? '创建中...' : '创建会议'}
              </Button>

              {createdId && (
                <div className="p-3 rounded text-xs" style={{ backgroundColor: 'var(--clr-gray-10)', color: 'var(--clr-text-primary)' }}>
                  会议已创建: <strong>{createdId}</strong>
                  <Button variant="outline" size="sm" className="ml-2" onClick={() => { setConfId(createdId); setView('checkin') }}>
                    前往签到
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {confId && (
            <Card>
              <CardContent className="p-4 space-y-2">
                <h4 className="text-xs font-semibold" style={{ color: 'var(--clr-text-secondary)' }}>邀请参会 (当前会议: {confId})</h4>
                <Button variant="outline" size="sm" onClick={handleInvite}>发送邀请(默认3人)</Button>
                {inviteResult && (
                  <p className="text-xs" style={{ color: 'var(--clr-text-secondary)' }}>
                    已邀请: {inviteResult.invited_count || inviteResult.end_to_end_trace?.length} 人
                  </p>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {view === 'checkin' && (
        <div className="space-y-4 max-w-lg">
          <Card>
            <CardContent className="p-4 space-y-3">
              <h3 className="text-sm font-semibold" style={{ color: 'var(--clr-text-primary)' }}>签到管理</h3>

              <div className="space-y-1">
                <label className="text-xs font-medium" style={{ color: 'var(--clr-text-secondary)' }}>会议ID</label>
                <Input value={confId} onChange={e => setConfId(e.target.value)} placeholder="输入会议ID" />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium" style={{ color: 'var(--clr-text-secondary)' }}>HCP ID</label>
                <Input value={checkinHcpId} onChange={e => setCheckinHcpId(e.target.value)} placeholder="如 hcp-001" />
              </div>

              <Button onClick={handleCheckin} disabled={!confId || !checkinHcpId}>
                手动签到
              </Button>

              {checkinResult && (
                <div className="p-3 rounded text-xs space-y-1" style={{ backgroundColor: 'var(--clr-gray-10)', color: 'var(--clr-text-primary)' }}>
                  <p>状态: {checkinResult.status}</p>
                  <p>签到人数: {checkinResult.checkin_count}</p>
                  <p>签到率: {checkinResult.invited_count ? ((checkinResult.checkin_count / checkinResult.invited_count) * 100).toFixed(1) : '-'}%</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {view === 'analytics' && (
        <div className="space-y-4 max-w-lg">
          <Card>
            <CardContent className="p-4 space-y-3">
              <h3 className="text-sm font-semibold" style={{ color: 'var(--clr-text-primary)' }}>会议分析</h3>

              <div className="space-y-1">
                <label className="text-xs font-medium" style={{ color: 'var(--clr-text-secondary)' }}>会议ID</label>
                <Input value={analyticsId} onChange={e => setAnalyticsId(e.target.value)} placeholder="输入会议ID" />
              </div>

              <Button onClick={handleAnalytics} disabled={!analyticsId && !confId}>
                查看分析
              </Button>

              {analyticsLoading && (
                <p className="text-xs" style={{ color: 'var(--clr-text-secondary)' }}>加载中...</p>
              )}

              {analyticsData && (
                <>
                  {analyticsData.data_trace && (
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3 rounded text-center" style={{ backgroundColor: 'var(--clr-gray-10)' }}>
                        <div className="text-2xl font-bold" style={{ color: 'var(--clr-brand)' }}>{analyticsData.data_trace.checkin_rate}%</div>
                        <div className="text-xs mt-1" style={{ color: 'var(--clr-text-secondary)' }}>签到率</div>
                      </div>
                      <div className="p-3 rounded text-center" style={{ backgroundColor: 'var(--clr-gray-10)' }}>
                        <div className="text-2xl font-bold" style={{ color: 'var(--clr-success)' }}>{analyticsData.data_trace.average_stay_minutes}</div>
                        <div className="text-xs mt-1" style={{ color: 'var(--clr-text-secondary)' }}>平均停留(分)</div>
                      </div>
                      <div className="p-3 rounded text-center" style={{ backgroundColor: 'var(--clr-gray-10)' }}>
                        <div className="text-2xl font-bold" style={{ color: 'var(--clr-warning)' }}>{analyticsData.data_trace.interaction_participation_rate}%</div>
                        <div className="text-xs mt-1" style={{ color: 'var(--clr-text-secondary)' }}>互动参与率</div>
                      </div>
                      <div className="p-3 rounded text-center" style={{ backgroundColor: 'var(--clr-gray-10)' }}>
                        <div className="text-2xl font-bold" style={{ color: 'var(--clr-text-primary)' }}>{analyticsData.data_trace.replay_views}</div>
                        <div className="text-xs mt-1" style={{ color: 'var(--clr-text-secondary)' }}>回放观看</div>
                      </div>
                    </div>
                  )}

                  {analyticsData.meeting && (
                    <div className="text-xs space-y-1 p-3 rounded" style={{ backgroundColor: 'var(--clr-gray-10)' }}>
                      <p><strong>会议:</strong> {analyticsData.meeting.title}</p>
                      <p><strong>类型:</strong> {analyticsData.meeting.type}</p>
                      <p><strong>状态:</strong> {analyticsData.meeting.status}</p>
                      <p><strong>邀请数:</strong> {analyticsData.meeting.invited_count}</p>
                      <p><strong>签到数:</strong> {analyticsData.meeting.checkin_count}</p>
                      <p><strong>讲者:</strong> {analyticsData.meeting.speaker || '-'}</p>
                    </div>
                  )}

                  {analyticsData.compliance_retention && (
                    <div className="p-3 rounded text-xs" style={{ backgroundColor: 'var(--clr-gray-10)', color: 'var(--clr-text-secondary)' }}>
                      合规归档: {analyticsData.compliance_retention.archived ? '已归档' : '未归档'} |
                      追踪记录: {analyticsData.compliance_retention.trace_count} 条 |
                      保留策略: {analyticsData.compliance_retention.retention_policy}
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
