import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { Card, CardContent } from "../ui/Card"
import { Button } from "../ui/Button"
import type { AbilityAssessment } from "../../api/mockCoach"

interface Props {
  data: AbilityAssessment
}

const tickStyle = { fontSize: '12px', color: 'var(--clr-text-secondary)' }

export default function AbilityRadar({ data }: Props) {
  const chartData = data.dimensions.map(d => ({
    name: d.name,
    实际分数: d.score,
    目标分数: d.target,
  }))

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="pt-5">
          <div style={{ width: '100%', height: 360 }}>
            <ResponsiveContainer>
              <RadarChart data={chartData} cx="50%" cy="50%" outerRadius="70%">
                <PolarGrid stroke="var(--clr-gray-20)" />
                <PolarAngleAxis dataKey="name" tick={tickStyle} />
                <PolarRadiusAxis
                  angle={30}
                  domain={[0, 100]}
                  tick={{ fontSize: 10, fill: 'var(--clr-text-secondary)' }}
                  axisLine={false}
                />
                <Radar
                  name="目标分数"
                  dataKey="目标分数"
                  stroke="var(--clr-gray-50)"
                  fill="var(--clr-gray-50)"
                  fillOpacity={0.05}
                  strokeDasharray="6 3"
                />
                <Radar
                  name="实际分数"
                  dataKey="实际分数"
                  stroke="var(--clr-brand)"
                  fill="var(--clr-brand)"
                  fillOpacity={0.15}
                />
                <Legend
                  wrapperStyle={{ fontSize: '13px', color: 'var(--clr-text-primary)' }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <div className="text-center">
        <p className="text-sm" style={{ color: 'var(--clr-text-secondary)' }}>总体评分</p>
        <p className="text-5xl font-bold" style={{ color: 'var(--clr-brand)' }}>{data.average}</p>
      </div>

      <Card>
        <CardContent className="pt-5">
          <h4 className="text-sm font-semibold mb-3" style={{ color: 'var(--clr-text-primary)' }}>改进建议</h4>
          <ul className="space-y-2">
            {data.suggestions.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-sm" style={{ color: 'var(--clr-text-secondary)' }}>
                <span className="font-medium shrink-0" style={{ color: 'var(--clr-brand)' }}>{i + 1}.</span>
                <span>→ {s}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Button className="w-full">开始新训练</Button>
    </div>
  )
}
