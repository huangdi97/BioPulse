import { useState, useRef, useCallback, useMemo, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { mockHcps } from '@/mock/hcps'
import { createVisit } from '@/api/visits'
import ComplianceScanner from '@/components/ComplianceScanner'
import ViolationDialog from '@/components/ViolationDialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/contexts/ToastContext'
import type { ScanResult } from '@/types'
import {
  ArrowLeft,
  User,
  Building2,
  ChevronDown,
  Send,
  RotateCw,
  CheckCircle2,
  XCircle,
  Circle,
  MapPin,
  Image as ImageIcon,
  Crosshair,
  AlertCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import PhotoUploader from '@/components/PhotoUploader'
import client from '@/api/client'

const VISIT_TYPES = ['实地拜访', '电话拜访', '线上会议', '其他']

export default function VisitNew() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { toast } = useToast()
  const hcpId = parseInt(searchParams.get('hcpId') ?? '0')
  const hcp = useMemo(() => mockHcps.find((h) => h.id === hcpId) ?? null, [hcpId])

  const [visitType, setVisitType] = useState(VISIT_TYPES[0])
  const [content, setContent] = useState('')
  const [typeOpen, setTypeOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const [scanResult, setScanResult] = useState<ScanResult>({
    passed: true,
    riskLevel: 'low',
    violations: [],
    score: 100,
  })
  const [isScanning, setIsScanning] = useState(false)
  const [showViolationDialog, setShowViolationDialog] = useState(false)

  const [photos, setPhotos] = useState<File[]>([]), [location, setLocation] = useState(''), [locationMode, setLocationMode] = useState('auto'), [settings, setSettings] = useState<Record<string,string>>({})

  const validateField = useCallback((field: string, value: string) => {
    switch (field) {
      case 'content':
        if (!value.trim()) return '请输入拜访内容'
        if (value.trim().length < 5) return '拜访内容至少需要5个字'
        return ''
      case 'visitType':
        if (!value) return '请选择拜访方式'
        return ''
      default:
        return ''
    }
  }, [])

  const validateAll = useCallback((): boolean => {
    const newErrors: Record<string, string> = {}
    const contentError = validateField('content', content)
    if (contentError) newErrors.content = contentError
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [content, validateField])

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value
    setContent(val)
    setIsScanning(true)
    if (touched.content) {
      setErrors((prev) => ({ ...prev, content: validateField('content', val) }))
    }
    const ta = e.target
    ta.style.height = 'auto'
    ta.style.height = Math.max(72, ta.scrollHeight) + 'px'
  }

  const handleContentBlur = () => {
    setTouched((prev) => ({ ...prev, content: true }))
    setErrors((prev) => ({ ...prev, content: validateField('content', content) }))
  }

  const handleScanResult = useCallback((result: ScanResult) => {
    setScanResult(result)
    setIsScanning(false)
  }, [])

  const uploadPhotos = async () => {
    const urls: string[] = []
    for (const f of photos) {
      const fd = new FormData()
      fd.append('file', f)
      const r = await client.post('/api/cloud/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      if ((r as any)?.url) urls.push((r as any).url)
    }
    return urls
  }
  useEffect(() => { client.get('/api/cloud/admin/settings').then((res: any) => {
    if (res?.data) setSettings(res.data)
    if (res?.data?.location_mode) setLocationMode(res.data.location_mode)
  }).catch(() => {}) }, [])
  const getLocation = () => {
    if (!navigator.geolocation) return setLocation('浏览器不支持定位')
    navigator.geolocation.getCurrentPosition(
      (p) => setLocation(`${p.coords.latitude.toFixed(6)}, ${p.coords.longitude.toFixed(6)}`),
      () => setLocation('无法获取位置')
    )
  }
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setTouched({ content: true, visitType: true })
    if (!validateAll()) return
    if (!scanResult.passed) { setShowViolationDialog(true); return }
    setSubmitting(true)
    try {
      const photoUrls = await uploadPhotos()
      const record = await createVisit({ hcpId: hcp!.id, hcpName: hcp!.name, content: content.trim(), visitType, evidence_photos: photoUrls, location, location_mode: locationMode })
      toast.success('拜访记录已成功保存')
      setTimeout(() => navigate(`/rep/visits/${record.id}`), 300)
    } catch {
      toast.error('拜访记录保存失败，请重试')
      setSubmitting(false)
    }
  }
  const handleForceSubmit = async () => {
    setShowViolationDialog(false)
    if (!content.trim() || !hcp) return
    setSubmitting(true)
    try {
      const photoUrls = await uploadPhotos()
      const record = await createVisit({ hcpId: hcp.id, hcpName: hcp.name, content: content.trim(), visitType, evidence_photos: photoUrls, location, location_mode: locationMode })
      toast.success('拜访记录已成功保存（已忽略合规警告）')
      setTimeout(() => navigate(`/rep/visits/${record.id}`), 300)
    } catch {
      toast.error('拜访记录保存失败，请重试')
      setSubmitting(false)
    }
  }

  const complianceIndicator = useMemo(() => {
    if (isScanning) {
      return {
        icon: RotateCw,
        text: '正在进行合规检查...',
        color: 'text-yellow-600',
        bg: 'bg-yellow-50 border-yellow-200',
      }
    }
    if (!content.trim()) {
      return {
        icon: Circle,
        text: '合规检查待开始',
        color: 'text-gray-400',
        bg: 'bg-gray-50 border-gray-200',
      }
    }
    if (!scanResult.passed) {
      return {
        icon: XCircle,
        text: '存在合规风险',
        color: 'text-red-600',
        bg: 'bg-red-50 border-red-200',
      }
    }
    return {
      icon: CheckCircle2,
      text: '合规检查通过',
      color: 'text-green-600',
      bg: 'bg-green-50 border-green-200',
    }
  }, [isScanning, scanResult.passed, content])

  if (!hcp) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <p>客户信息未找到</p>
        <Button variant="link" onClick={() => navigate('/rep/hcps')}>
          返回列表
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <ComplianceScanner content={content} onResult={handleScanResult} />

      <ViolationDialog
        open={showViolationDialog}
        violations={scanResult.violations}
        onModify={() => setShowViolationDialog(false)}
        onForceSubmit={handleForceSubmit}
      />

      <button
        onClick={() => navigate(`/rep/hcps/${hcpId}`)}
        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        返回客户详情
      </button>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">拜访客户</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
              <User className="h-6 w-6 text-primary" />
            </div>
            <div>
              <p className="font-semibold">{hcp.name}</p>
              <p className="flex items-center gap-1 text-xs text-muted-foreground">
                <Building2 className="h-3 w-3" />
                {hcp.hospital} · {hcp.dept}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">
              <span className="text-red-500 mr-1">*</span>拜访方式
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="relative">
              <button
                type="button"
                onClick={() => setTypeOpen(!typeOpen)}
                className="flex w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <span>{visitType}</span>
                <ChevronDown className="h-4 w-4 opacity-50" />
              </button>

              {typeOpen && (
                <div className="absolute z-10 mt-1 w-full rounded-md border bg-popover shadow-md">
                  {VISIT_TYPES.map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => {
                        setVisitType(type)
                        setTypeOpen(false)
                      }}
                      className={cn(
                        'w-full px-3 py-2 text-left text-sm hover:bg-accent',
                        visitType === type && 'font-medium text-primary'
                      )}
                    >
                      {type}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">
              <span className="text-red-500 mr-1">*</span>拜访内容
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div
              className={cn(
                'flex items-center gap-2 rounded-md border px-3 py-2 text-sm',
                complianceIndicator.bg
              )}
            >
              <complianceIndicator.icon
                className={cn(
                  'h-4 w-4 flex-shrink-0',
                  complianceIndicator.color,
                  isScanning && 'animate-spin'
                )}
              />
              <span className={complianceIndicator.color}>
                {complianceIndicator.text}
              </span>
            </div>

            <div className="relative">
              <textarea
                ref={textareaRef}
                value={content}
                onChange={handleContentChange}
                onBlur={handleContentBlur}
                placeholder="请输入拜访内容，描述本次拜访的详细信息..."
                className={cn(
                  'w-full resize-none rounded-md border bg-background px-3 py-2 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                  errors.content ? 'border-red-500 focus:ring-red-500' : 'border-input'
                )}
                rows={3}
                style={{ minHeight: '72px' }}
              />
              <span className="absolute bottom-2 right-3 text-xs text-muted-foreground pointer-events-none">
                {content.length} 字
              </span>
            </div>

            {errors.content && (
              <div className="flex items-center gap-1 text-xs text-red-500">
                <AlertCircle className="h-3 w-3" />
                {errors.content}
              </div>
            )}
          </CardContent>
        </Card>

        {locationMode !== 'off' && (
          <Card>
            <CardHeader className="pb-3"><CardTitle className="text-base flex items-center gap-2"><MapPin className="h-4 w-4" />签到定位</CardTitle></CardHeader>
            <CardContent>
              {locationMode === 'auto' ? (<div className="flex items-center gap-2">
                  <Button type="button" variant="outline" size="sm" onClick={getLocation}><Crosshair className="h-4 w-4 mr-1" />{location ? '重新获取位置' : '获取当前位置'}</Button>
                  {location && <span className="text-sm text-muted-foreground">{location}</span>}
                </div>) : (<input type="text" value={location} onChange={(e) => setLocation(e.target.value)} placeholder="请输入签到地址" className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />)}
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader className="pb-3"><CardTitle className="text-base flex items-center gap-2"><ImageIcon className="h-4 w-4" />现场照片</CardTitle></CardHeader>
          <CardContent>
            <PhotoUploader photos={photos} onPhotosChange={setPhotos} />
          </CardContent>
        </Card>

        <Button
          type="submit"
          disabled={submitting}
          className="w-full"
          size="lg"
          loading={submitting}
        >
          <Send className="h-4 w-4 mr-2" />
          {submitting ? '提交中...' : '提 交'}
        </Button>
      </form>
    </div>
  )
}
