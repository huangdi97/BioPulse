import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Search, TrendingUp, BarChart3, Lightbulb } from 'lucide-react'

export default function ResearchPanel() {
  const [analysis] = useState([
    { keyword: '心内科新药', competitors: 3, marketSize: '12亿', growth: '+15%' },
    { keyword: '糖尿病治疗', competitors: 5, marketSize: '28亿', growth: '+8%' },
    { keyword: '肿瘤免疫', competitors: 2, marketSize: '35亿', growth: '+25%' },
  ])

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">研究分析面板</h2>

      <Card>
        <CardHeader><CardTitle className="text-base flex items-center gap-2"><Search className="h-4 w-4 text-blue-500" />市场研究</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {analysis.map((item) => (
            <div key={item.keyword} className="p-3 rounded-lg border">
              <p className="text-sm font-semibold">{item.keyword}</p>
              <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                <span className="flex items-center gap-1"><BarChart3 className="h-3 w-3" />竞品: {item.competitors}家</span>
                <span>市场规模: {item.marketSize}</span>
                <span className="flex items-center gap-1 text-green-600"><TrendingUp className="h-3 w-3" />{item.growth}</span>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base flex items-center gap-2"><Lightbulb className="h-4 w-4 text-yellow-500" />AI 洞察</CardTitle></CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li>· 心内科领域竞争加剧，建议加强学术推广投入</li>
            <li>· 肿瘤免疫领域增长迅速，可考虑作为重点突破方向</li>
            <li>· 糖尿病治疗市场成熟，差异化策略是关键</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
