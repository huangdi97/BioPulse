import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/Card"
import { Button } from "../../components/ui/Button"
import { Input } from "../../components/ui/Input"
import { cn } from "../../lib/utils"
import { useAuth } from "../../auth/AuthContext"
import { changePasswordApi } from "../../api/client"

type TabId = "profile" | "api" | "notify" | "about"

interface ApiEndpoint {
  name: string
  url: string
  online: boolean
}

const API_BASE = import.meta.env.VITE_CLOUD_API || "http://localhost:8000"

const SIDEBAR_ITEMS: { id: TabId; label: string }[] = [
  { id: "profile", label: "个人信息" },
  { id: "api", label: "API 配置" },
  { id: "notify", label: "通知设置" },
  { id: "about", label: "关于" },
]

const NOTIFY_ITEMS = [
  { key: "compliance", label: "合规预警推送", desc: "接收合规风险预警通知" },
  { key: "visit", label: "拜访提醒", desc: "即将进行的客户拜访提醒" },
  { key: "task", label: "任务到期通知", desc: "任务截止前发送提醒" },
  { key: "announcement", label: "系统公告", desc: "系统更新与维护公告" },
  { key: "dailyBrief", label: "每日数据简报", desc: "每日工作数据汇总推送" },
] as const

const ABOUT_ROWS = [
  { label: "系统名称", value: "BioPulse · 生命科学销售 AI 工作台" },
  { label: "版本号", value: "v1.0.0 (Build 2026-06-05)" },
  { label: "设计系统版本", value: "1.0" },
  { label: "技术支持", value: "support@biopulse.ai" },
] as const

const DEFAULT_ENDPOINTS: ApiEndpoint[] = [
  { name: "Cloud API", url: `${API_BASE}`, online: true },
  { name: "Intel API", url: `${import.meta.env.VITE_INTEL_API || "http://localhost:8006"}`, online: false },
  { name: "Assistant API", url: `${import.meta.env.VITE_ASSISTANT_API || "http://localhost:8003"}`, online: false },
  { name: "Opportunity API", url: `${import.meta.env.VITE_OPPORTUNITY_API || "http://localhost:8002"}`, online: true },
  { name: "Sales Assistant API", url: `${import.meta.env.VITE_SALES_ASSISTANT_API || "http://localhost:8004"}`, online: false },
  { name: "Sales Coach API", url: `${import.meta.env.VITE_SALES_COACH_API || "http://localhost:8001"}`, online: false },
]

export default function SettingsPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<TabId>("profile")

  const [endpoints, setEndpoints] = useState<ApiEndpoint[]>(DEFAULT_ENDPOINTS)
  const [notifications, setNotifications] = useState({
    compliance: true,
    visit: true,
    task: false,
    announcement: true,
    dailyBrief: false,
  })

  const testConnection = (index: number) => {
    setEndpoints(prev =>
      prev.map((ep, i) => (i === index ? { ...ep, online: !ep.online } : ep))
    )
  }

  const updateEndpointUrl = (index: number, url: string) => {
    setEndpoints(prev =>
      prev.map((ep, i) => (i === index ? { ...ep, url } : ep))
    )
  }

  return (
    <div className="flex gap-6 max-w-4xl">
      <nav className="w-44 shrink-0 space-y-1">
        {SIDEBAR_ITEMS.map(item => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={cn(
              "w-full text-left px-3 py-2 rounded-md text-sm transition-colors",
              activeTab === item.id
                ? "bg-[var(--clr-surface-selected)] text-[var(--clr-brand)] font-medium"
                : "text-[var(--clr-text-secondary)] hover:bg-[var(--clr-surface-hover)]"
            )}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <div className="flex-1 min-w-0">
        {activeTab === "profile" && (
          <ProfileTab user={user} />
        )}
        {activeTab === "api" && (
          <ApiTab
            endpoints={endpoints}
            onUpdateUrl={updateEndpointUrl}
            onTest={testConnection}
          />
        )}
        {activeTab === "notify" && (
          <NotifyTab
            notifications={notifications}
            setNotifications={setNotifications}
          />
        )}
        {activeTab === "about" && <AboutTab />}
      </div>
    </div>
  )
}

function ProfileTab({ user }: { user: { id: number; username: string } | null }) {
  const [oldPassword, setOldPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [notAvailable, setNotAvailable] = useState(false)

  const displayName = user?.username ?? ""
  const avatarChar = displayName.charAt(0) || "?"

  const handleChangePassword = async () => {
    setError(null)
    setSuccess(false)
    setNotAvailable(false)

    if (!oldPassword || !newPassword || !confirmPassword) {
      setError("请填写所有密码字段")
      return
    }
    if (newPassword.length < 6) {
      setError("新密码长度至少为 6 个字符")
      return
    }
    if (newPassword !== confirmPassword) {
      setError("两次输入的新密码不一致")
      return
    }

    setLoading(true)
    try {
      await changePasswordApi(user!.username, oldPassword, newPassword)
      setSuccess(true)
      setOldPassword("")
      setNewPassword("")
      setConfirmPassword("")
    } catch (e) {
      const msg = e instanceof Error ? e.message : "修改密码失败"
      // 404 means the backend does not have this endpoint yet
      if (msg.includes("404") || msg.includes("Not Found") || msg.includes("not found")) {
        setNotAvailable(true)
      } else {
        setError(msg)
      }
    } finally {
      setLoading(false)
    }
  }

  // If the backend endpoint doesn't exist, show a teaser placeholder
  if (notAvailable) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>个人信息</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-[var(--clr-brand)] text-[var(--clr-text-inverse)] flex items-center justify-center text-xl font-semibold">
                {avatarChar}
              </div>
              <div>
                <p className="text-sm font-medium text-[var(--clr-text-primary)]">{displayName || "未登录"}</p>
                <p className="text-xs text-[var(--clr-text-secondary)]">ID: {user?.id ?? "-"}</p>
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-[var(--clr-text-primary)]">用户名</label>
              <Input value={displayName} readOnly />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>修改密码</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-6 text-center">
              <span className="text-3xl mb-3">🚧</span>
              <p className="text-sm font-medium text-[var(--clr-text-primary)]">密码修改功能即将推出</p>
              <p className="text-xs text-[var(--clr-text-secondary)] mt-1">敬请期待后续版本更新</p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>个人信息</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-[var(--clr-brand)] text-[var(--clr-text-inverse)] flex items-center justify-center text-xl font-semibold">
              {avatarChar}
            </div>
            <div>
              <p className="text-sm font-medium text-[var(--clr-text-primary)]">{displayName || "未登录"}</p>
              <p className="text-xs text-[var(--clr-text-secondary)]">ID: {user?.id ?? "-"}</p>
            </div>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-[var(--clr-text-primary)]">用户名</label>
            <Input value={displayName} readOnly />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>修改密码</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-[var(--clr-text-primary)]">旧密码</label>
            <Input
              type="password"
              value={oldPassword}
              onChange={e => setOldPassword(e.target.value)}
              placeholder="请输入旧密码"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-[var(--clr-text-primary)]">新密码</label>
            <Input
              type="password"
              value={newPassword}
              onChange={e => setNewPassword(e.target.value)}
              placeholder="请输入新密码"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-[var(--clr-text-primary)]">确认新密码</label>
            <Input
              type="password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              placeholder="请再次输入新密码"
            />
          </div>

          {error && (
            <p className="text-xs text-[var(--clr-error)]">{error}</p>
          )}
          {success && (
            <p className="text-xs text-[var(--clr-success)]">✅ 密码修改成功</p>
          )}

          <Button onClick={handleChangePassword} disabled={loading}>
            {loading ? "修改中..." : "修改密码"}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

function ApiTab({
  endpoints,
  onUpdateUrl,
  onTest,
}: {
  endpoints: ApiEndpoint[]
  onUpdateUrl: (i: number, url: string) => void
  onTest: (i: number) => void
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>API 配置</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {endpoints.map((ep, i) => (
          <div key={ep.name} className="flex items-center gap-3">
            <span className="w-32 text-sm text-[var(--clr-text-primary)] shrink-0">{ep.name}</span>
            <Input
              value={ep.url}
              onChange={e => onUpdateUrl(i, e.target.value)}
              className="flex-1"
            />
            <span
              className={cn("w-2.5 h-2.5 rounded-full shrink-0", ep.online ? "bg-[var(--clr-success)]" : "bg-[var(--clr-error)]")}
              title={ep.online ? "在线" : "离线"}
            />
            <Button variant="outline" size="sm" onClick={() => onTest(i)}>测试连接</Button>
          </div>
        ))}
        <Button className="mt-2">保存</Button>
      </CardContent>
    </Card>
  )
}

function NotifyTab({
  notifications,
  setNotifications,
}: {
  notifications: { compliance: boolean; visit: boolean; task: boolean; announcement: boolean; dailyBrief: boolean }
  setNotifications: (n: typeof notifications) => void
}) {
  const toggle = (key: keyof typeof notifications) => {
    setNotifications({ ...notifications, [key]: !notifications[key] })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>通知设置</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {NOTIFY_ITEMS.map(item => (
          <div key={item.key} className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-[var(--clr-text-primary)]">{item.label}</p>
              <p className="text-xs text-[var(--clr-text-secondary)] mt-0.5">{item.desc}</p>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={notifications[item.key]}
              onClick={() => toggle(item.key)}
              className={cn(
                "relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors",
                notifications[item.key] ? "bg-[var(--clr-brand)]" : "bg-[var(--clr-gray-30)]"
              )}
            >
              <span
                className={cn(
                  "pointer-events-none inline-block h-4 w-4 rounded-full bg-[var(--clr-white)] shadow transition-transform",
                  notifications[item.key] ? "translate-x-4" : "translate-x-0"
                )}
              />
            </button>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

function AboutTab() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>关于</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {ABOUT_ROWS.map(row => (
          <div key={row.label} className="flex gap-4">
            <span className="w-28 text-sm text-[var(--clr-text-secondary)] shrink-0">{row.label}</span>
            <span className="text-sm text-[var(--clr-text-primary)]">{row.value}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
