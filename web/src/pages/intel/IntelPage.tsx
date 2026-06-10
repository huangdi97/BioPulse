import { useState } from "react"
import PaperSearchTab from "../../components/intel/PaperSearchTab"
import PiProfileTab from "../../components/intel/PiProfileTab"
import TargetHeatmapTab from "../../components/intel/TargetHeatmapTab"
import CompetitorIntelTab from "../../components/intel/CompetitorIntelTab"

const TABS = ['论文搜索', 'PI画像', '靶点热度', '竞品情报'] as const

export default function IntelPage() {
  const [tab, setTab] = useState(0)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold" style={{color: 'var(--clr-text-primary)'}}>制药情报</h1>
        <p className="text-sm mt-1" style={{color: 'var(--clr-text-secondary)'}}>论文检索、PI画像与靶点热度分析</p>
      </div>

      <div className="flex gap-1 p-1 rounded-lg w-fit" style={{backgroundColor: 'var(--clr-gray-10)'}}>
        {TABS.map((t, i) => (
          <button
            key={t}
            onClick={() => setTab(i)}
            className={`px-4 py-1.5 text-sm rounded-md transition-colors ${
              i === tab ? 'bg-white shadow-sm font-medium' : ''
            }`}
            style={{color: i === tab ? 'var(--clr-text-primary)' : 'var(--clr-text-secondary)'}}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 0 && <PaperSearchTab />}
      {tab === 1 && <PiProfileTab />}
      {tab === 2 && <TargetHeatmapTab />}
      {tab === 3 && <CompetitorIntelTab />}
    </div>
  )
}
