import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/Card"
import { Button } from "../../components/ui/Button"
import { Input } from "../../components/ui/Input"
import { Badge } from "../../components/ui/Badge"
import { cn } from "../../lib/utils"

type TabId = "profile" | "api" | "notify" | "about"

interface ApiEndpoint {
  name: string
  url: string
  online: boolean
}

const SIDEBAR_ITEMS: { id: TabId; label: string }[] = [
  { id: "profile", label: "个人信息" },
  { id: "api", label: "API 配置" },
  { id: "notify", label: "通知设置" },
  { id: "about", label: "关于" },
]

const ROLE_MAP = { admin: "管理员", manager: "经理", staff: "员工" } as const

const NOTIFY_ITEMS = [
  { key: "compliance", label: "合规预警推送", desc: "接收合规风险预警通知" },
  { key: "visit", label: "拜访提醒", desc: "即将进行的客户拜访提醒" },
  { key: "task", label: "任务到期通知", desc: "任务截止前发送提醒" },
  { key: "announcement", label: "系统公告", desc: "系统更新与维护公告" },
  { key: "dailyBrief", label: "每日数据简报", desc: "每日工作数据汇总推送" },
] as const

const ABOUT_ROWS = [
  { label: "系统名称", value: "一云四端 · 生命科学销售 AI 工作台" },
  { label: "版本号", value: "v1.0.0 (Build 2026-06-05)" },
  { label: "设计系统版本", value: "1.0" },
  { label: "技术支持", value: "support@yysd.io" },
] as const

const DEFAULT_ENDPOINTS: ApiEndpoint[] = [
  { name: "Cloud API", url: "http://localhost:8000", online: true },
  { name: "Assistant API", url: "http://localhost:8003", online: false },
  { name: "Opportunity API", url: "http://localhost:8002", online: true },
  { name: "Sales Assistant API", url: "http://localhost:8004", online: false },
  { name: "Sales Coach API", url: "http://localhost:8001", online: false },
]

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabId>("profile")

  const [profile, setProfile] = useState({
    name: "张明",
    email: "zhangming@yysd.io",
    role: "admin" as keyof typeof ROLE_MAP,
    institution: "一云四端科技有限公司",
  })

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
          <ProfileTab profile={profile} setProfile={setProfile} />
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

function ProfileTab({
  profile,
  setProfile,
}: {
  profile: { name: string; email: string; role: keyof typeof ROLE_MAP; institution: string }
  setProfile: (p: typeof profile) => void
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>个人信息</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-[var(--clr-brand)] text-[var(--clr-text-inverse)] flex items-center justify-center text-xl font-semibold">
            {profile.name.charAt(0)}
          </div>
          <div>
            <p className="text-sm font-medium text-[var(--clr-text-primary)]">{profile.name}</p>
            <p className="text-xs text-[var(--clr-text-secondary)]">{profile.email}</p>
          </div>
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-[var(--clr-text-primary)]">姓名</label>
          <Input value={profile.name} onChange={e => setProfile({ ...profile, name: e.target.value })} />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-[var(--clr-text-primary)]">邮箱</label>
          <Input value={profile.email} readOnly />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-[var(--clr-text-primary)]">角色</label>
          <Badge
            variant={
              profile.role === "admin" ? "default" : profile.role === "manager" ? "warning" : "neutral"
            }
          >
            {ROLE_MAP[profile.role]}
          </Badge>
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-[var(--clr-text-primary)]">所属机构</label>
          <Input
            value={profile.institution}
            onChange={e => setProfile({ ...profile, institution: e.target.value })}
          />
        </div>
        <Button>保存</Button>
      </CardContent>
    </Card>
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
