import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'
import client from '@/api/client'
import { Save, Loader2 } from 'lucide-react'

interface SystemSettings {
  watermark_enabled: boolean
  checkin_location: string
  storage_location: string
}

export default function Settings() {
  const [settings, setSettings] = useState<SystemSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    client.get('/api/cloud/admin/settings').then((res) => {
      setSettings(res.data)
      setLoading(false)
    })
  }, [])

  const handleSave = async () => {
    if (!settings) return
    setSaving(true)
    try {
      await client.put('/api/cloud/admin/settings', settings)
      alert('保存成功')
    } catch {
      alert('保存失败')
    } finally {
      setSaving(false)
    }
  }

  if (loading || !settings) {
    return (
      <div className="flex items-center justify-center h-48 text-muted-foreground text-sm">
        加载中...
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">系统配置</h1>

      <Card>
        <CardHeader>
          <CardTitle>照片水印</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              {settings.watermark_enabled ? '已启用' : '已禁用'}
            </span>
            <Switch
              checked={settings.watermark_enabled}
              onCheckedChange={(checked) =>
                setSettings({ ...settings, watermark_enabled: checked })
              }
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>签到定位</CardTitle>
        </CardHeader>
        <CardContent>
          <RadioGroup
            value={settings.checkin_location}
            onValueChange={(value) =>
              setSettings({ ...settings, checkin_location: value })
            }
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="auto" id="auto" />
              <Label htmlFor="auto">自动获取</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="manual" id="manual" />
              <Label htmlFor="manual">手动填写</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="disabled" id="disabled" />
              <Label htmlFor="disabled">关闭</Label>
            </div>
          </RadioGroup>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>存储位置</CardTitle>
        </CardHeader>
        <CardContent>
          <RadioGroup
            value={settings.storage_location}
            onValueChange={(value) =>
              setSettings({ ...settings, storage_location: value })
            }
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="local" id="local" />
              <Label htmlFor="local">本地服务器</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="oss" id="oss" disabled />
              <Label htmlFor="oss" className="text-muted-foreground">
                对象存储 <span className="text-xs">(即将上线)</span>
              </Label>
            </div>
          </RadioGroup>
        </CardContent>
      </Card>

      <div className="flex justify-center pt-4">
        <Button onClick={handleSave} disabled={saving}>
          {saving ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          保存
        </Button>
      </div>
    </div>
  )
}
