import { useState, useEffect } from "react"
import { X, ChevronRight, ChevronLeft, Check } from "lucide-react"
import { Button } from "../ui/Button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "../ui/Card"

const STORAGE_KEY = "onboarding_done"

interface Step {
  title: string
  description: string
  features?: string[]
}

const STEPS: Step[] = [
  {
    title: "欢迎使用一云四端",
    description:
      "一云四端是专为生命科学领域打造的全场景销售 AI 工作台，融合医药代表、科研销售、合规管理和销售教练四大核心模块，助您轻松应对复杂的销售场景。",
    features: ["医药代表工作台", "科研销售助手", "合规风险管理", "销售能力教练"],
  },
  {
    title: "核心功能",
    description:
      "智能拜访管理、合规风险预警、客户洞察分析、销售能力评估与训练，全方位提升销售效率与合规水平。",
    features: ["实时数据看板", "智能合规预警", "客户洞察分析", "销售能力雷达"],
  },
  {
    title: "开始使用",
    description:
      "一切就绪！您可以随时在设置中调整偏好。现在，开始探索一云四端为您带来的全新工作体验吧。",
  },
]

export default function OnboardingGuide() {
  const [step, setStep] = useState(0)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const done = localStorage.getItem(STORAGE_KEY)
    if (!done) {
      setVisible(true)
    }
  }, [])

  const dismiss = () => {
    localStorage.setItem(STORAGE_KEY, "true")
    setVisible(false)
  }

  const isLast = step === STEPS.length - 1

  if (!visible) return null

  const current = STEPS[step]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <Card className="w-full max-w-lg mx-4 shadow-[var(--shadow-modal)]">
        <CardHeader className="flex-row items-start justify-between">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-[var(--clr-brand)] text-[var(--clr-text-inverse)] text-xs font-semibold">
                {step + 1}
              </span>
              <span className="text-xs text-[var(--clr-text-secondary)]">
                / {STEPS.length}
              </span>
            </div>
            <CardTitle>{current.title}</CardTitle>
            <CardDescription>{current.description}</CardDescription>
          </div>
          <button
            type="button"
            onClick={dismiss}
            className="p-1 rounded-md text-[var(--clr-text-secondary)] hover:bg-[var(--clr-surface-hover)] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </CardHeader>
        <CardContent>
          {current.features && (
            <div className="grid grid-cols-2 gap-2">
              {current.features.map((feat) => (
                <div
                  key={feat}
                  className="flex items-center gap-2 px-3 py-2 rounded-md bg-[var(--clr-surface-card-alt)] text-sm text-[var(--clr-text-primary)]"
                >
                  <Check className="w-4 h-4 text-[var(--clr-success)] shrink-0" />
                  {feat}
                </div>
              ))}
            </div>
          )}
          <div className="flex gap-1.5 mt-4 justify-center">
            {STEPS.map((_, i) => (
              <div
                key={i}
                className={`h-1.5 rounded-full transition-all ${
                  i === step
                    ? "w-6 bg-[var(--clr-brand)]"
                    : "w-1.5 bg-[var(--clr-gray-30)]"
                }`}
              />
            ))}
          </div>
        </CardContent>
        <CardFooter className="justify-between">
          <div>
            <button
              type="button"
              onClick={dismiss}
              className="text-sm text-[var(--clr-text-secondary)] hover:text-[var(--clr-text-primary)] transition-colors"
            >
              跳过引导
            </button>
          </div>
          <div className="flex items-center gap-2">
            {step > 0 && (
              <Button variant="outline" size="sm" onClick={() => setStep(step - 1)}>
                <ChevronLeft className="w-4 h-4" />
                上一步
              </Button>
            )}
            {isLast ? (
              <Button size="sm" onClick={dismiss}>
                开始使用
                <Check className="w-4 h-4" />
              </Button>
            ) : (
              <Button size="sm" onClick={() => setStep(step + 1)}>
                下一步
                <ChevronRight className="w-4 h-4" />
              </Button>
            )}
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}
