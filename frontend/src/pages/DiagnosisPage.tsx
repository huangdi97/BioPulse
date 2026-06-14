import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import AiCapabilityCard from '@/components/ai/AiCapabilityCard'
import { Microscope, FileText, Pill, Stethoscope } from 'lucide-react'

export default function DiagnosisPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 500)
    return () => clearTimeout(t)
  }, [])

  return (
    <div className="space-y-4">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        ← 返回
      </button>

      <div>
        <h1 className="text-xl font-bold">AI 诊断能力</h1>
        <p className="text-sm text-muted-foreground mt-1">基于智能体分析的患者诊断辅助工具</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Stethoscope className="h-4 w-4 text-blue-500" />
            诊断摘要
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2 animate-pulse">
              <div className="h-3 bg-muted rounded w-3/4" />
              <div className="h-3 bg-muted rounded w-1/2" />
            </div>
          ) : (
            <p className="text-sm text-muted-foreground leading-relaxed">
              基于患者历史数据和当前症状，AI 模型已完成初步诊断分析。建议结合临床检查结果进行综合判断。
            </p>
          )}
        </CardContent>
      </Card>

      <div>
        <h2 className="text-sm font-semibold text-muted-foreground mb-3">诊断辅助工具</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <AiCapabilityCard
            icon={<Microscope className="h-5 w-5 text-blue-600" />}
            title="影像分析"
            description="基于深度学习的医学影像识别与病灶检测"
            status="simulated"
          />
          <AiCapabilityCard
            icon={<FileText className="h-5 w-5 text-purple-600" />}
            title="病理报告"
            description="自动解析病理报告并提取关键诊断指标"
            status="simulated"
          />
          <AiCapabilityCard
            icon={<Pill className="h-5 w-5 text-green-600" />}
            title="用药建议"
            description="基于诊疗指南的个性化用药推荐"
            status="simulated"
          />
        </div>
      </div>
    </div>
  )
}
