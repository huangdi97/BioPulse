import { useState } from "react"
import { cn } from "../../lib/utils"

interface Plan {
  name: string
  price: string
  period: string
  desc: string
  highlighted: boolean
  features: string[]
  cta: string
}

const pharmaPlans: Plan[] = [
  {
    name: "入门版", price: "¥0", period: "/月",
    desc: "基础HCP管理 + 拜访记录 + 合规检查",
    highlighted: false,
    features: ["HCP 档案管理", "拜访记录追踪", "基础合规检查", "1 人使用"],
    cta: "立即咨询",
  },
  {
    name: "标准版", price: "¥299", period: "/人/月",
    desc: "入门版功能 + AI建议 + 合规预警 + 管理看板",
    highlighted: true,
    features: ["所有入门版功能", "AI 智能建议", "合规预警通知", "团队管理看板", "多角色权限"],
    cta: "立即咨询",
  },
  {
    name: "企业版", price: "定制报价", period: "",
    desc: "标准版 + API对接 + 专属合规规则 + 培训系统",
    highlighted: false,
    features: ["所有标准版功能", "API 系统对接", "专属合规规则引擎", "在线培训系统", "专属客户成功"],
    cta: "联系我们",
  },
]

const researchPlans: Plan[] = [
  {
    name: "标准版", price: "¥399", period: "/人/月",
    desc: "PI线索雷达 + 产品匹配Top3 + 报价管理 + 订单跟踪",
    highlighted: false,
    features: ["PI 线索雷达", "产品匹配 Top 3", "报价管理", "订单跟踪"],
    cta: "立即咨询",
  },
  {
    name: "高级版", price: "¥799", period: "/人/月",
    desc: "标准版 + AI全自动匹配 + 库存联动 + 高级情报分析",
    highlighted: true,
    features: ["所有标准版功能", "AI 全自动匹配", "库存联动", "高级情报分析", "专属数据看板"],
    cta: "立即咨询",
  },
]

const faqItems = [
  { q: "可以免费试用吗？", a: "入门版永久免费，无需信用卡。标准版和高级版均提供 14 天免费试用，试用期内可随时取消。" },
  { q: "如何升级或降级方案？", a: "您可以在后台设置页面随时升级或降级方案，差价按剩余天数计算，立即生效。" },
  { q: "是否支持定制化需求？", a: "企业版支持 API 对接、专属合规规则、定制培训等。请联系销售团队了解详情。" },
]

function PricingCard({ plan }: { plan: Plan }) {
  return (
    <div
      className={cn(
        "relative flex flex-col rounded-[var(--radius-xl)] bg-[var(--clr-surface-card)] p-6 shadow-[var(--shadow-card)] transition-shadow hover:shadow-[var(--shadow-raised)]",
        plan.highlighted && "border-2 border-[var(--clr-brand)]"
      )}
    >
      {plan.highlighted && (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-[var(--clr-brand)] px-3 py-0.5 text-xs font-medium text-[var(--clr-text-inverse)]">
          推荐
        </span>
      )}
      <h3 className="text-lg font-semibold text-[var(--clr-text-primary)]">{plan.name}</h3>
      <div className="mt-2 flex items-baseline gap-0.5">
        <span className="text-3xl font-bold text-[var(--clr-text-primary)]">{plan.price}</span>
        {plan.period && <span className="text-sm text-[var(--clr-text-secondary)]">{plan.period}</span>}
      </div>
      <p className="mt-1 text-sm text-[var(--clr-text-secondary)]">{plan.desc}</p>
      <ul className="mt-4 space-y-2 flex-1">
        {plan.features.map((f) => (
          <li key={f} className="flex items-center gap-2 text-sm text-[var(--clr-text-primary)]">
            <span className="text-[var(--clr-brand)] shrink-0">&#10003;</span>
            {f}
          </li>
        ))}
      </ul>
      <button
        className={cn(
          "mt-6 w-full rounded-md py-2.5 text-sm font-medium transition-colors",
          plan.highlighted
            ? "bg-[var(--clr-brand)] text-[var(--clr-text-inverse)] hover:bg-[var(--clr-brand-hover)]"
            : "border border-[var(--clr-border-default)] text-[var(--clr-text-primary)] hover:bg-[var(--clr-surface-hover)]"
        )}
      >
        {plan.cta}
      </button>
    </div>
  )
}

function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border-b border-[var(--clr-border-default)] last:border-0">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between py-4 text-left text-sm font-medium text-[var(--clr-text-primary)]"
      >
        {q}
        <span className={cn("text-[var(--clr-text-secondary)] text-xs transition-transform", open && "rotate-180")}>
          &#9660;
        </span>
      </button>
      {open && <p className="pb-4 text-sm text-[var(--clr-text-secondary)]">{a}</p>}
    </div>
  )
}

export default function PricingPage() {
  const [tab, setTab] = useState(0)

  return (
    <div className="mx-auto max-w-[1200px]">
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-[var(--clr-text-primary)]">定价方案</h1>
        <p className="mt-1 text-sm text-[var(--clr-text-secondary)]">
          选择适合您团队的工具，推动业务增长
        </p>
      </div>

      <div className="mt-6 flex justify-center">
        <div className="inline-flex rounded-lg bg-[var(--clr-gray-10)] p-0.5">
          {["医药代表", "科研销售"].map((t, i) => (
            <button
              key={t}
              onClick={() => setTab(i)}
              className={cn(
                "rounded-md px-5 py-1.5 text-sm font-medium transition-colors",
                i === tab
                  ? "bg-[var(--clr-white)] text-[var(--clr-text-primary)] shadow-[var(--shadow-border)]"
                  : "text-[var(--clr-text-secondary)] hover:text-[var(--clr-text-primary)]"
              )}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div
        className={cn(
          "mt-8 grid gap-5",
          tab === 0
            ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
            : "grid-cols-1 md:grid-cols-2 max-w-[820px] mx-auto"
        )}
      >
        {(tab === 0 ? pharmaPlans : researchPlans).map((plan) => (
          <PricingCard key={plan.name} plan={plan} />
        ))}
      </div>

      <div className="mt-16">
        <h2 className="text-center text-xl font-semibold text-[var(--clr-text-primary)]">常见问题</h2>
        <div className="mx-auto mt-6 max-w-[640px] rounded-[var(--radius-lg)] bg-[var(--clr-surface-card)] px-6 shadow-[var(--shadow-card)]">
          {faqItems.map(({ q, a }) => (
            <FaqItem key={q} q={q} a={a} />
          ))}
        </div>
      </div>
    </div>
  )
}
