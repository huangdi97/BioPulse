import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  fetchHealthScore,
  fetchUsageTrend,
  fetchAtRiskReps,
  fetchNPS,
  type AtRiskRep,
} from '@/api/adminCustomerSuccess'

export default function CustomerSuccess() {
  const [healthScore, setHealthScore] = useState<number | null>(null)
  const [usageTrend, setUsageTrend] = useState<string | null>(null)
  const [atRiskReps, setAtRiskReps] = useState<AtRiskRep[] | null>(null)
  const [nps, setNps] = useState<number | null>(null)

  useEffect(() => {
    let cancelled = false

    Promise.all([
      fetchHealthScore(),
      fetchUsageTrend(),
      fetchAtRiskReps(),
      fetchNPS(),
    ]).then(([hs, ut, ar, n]) => {
      if (!cancelled) {
        setHealthScore(hs)
        setUsageTrend(ut)
        setAtRiskReps(ar)
        setNps(n)
      }
    })

    return () => { cancelled = true }
  }, [])

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Health Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">
              {healthScore ?? '-'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              NPS Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">
              {nps ?? '-'}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Usage Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            {usageTrend ?? 'Loading...'}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">At-Risk Representatives</CardTitle>
        </CardHeader>
        <CardContent>
          {!atRiskReps ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : atRiskReps.length === 0 ? (
            <p className="text-muted-foreground">No at-risk representatives.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 font-medium">Name</th>
                  <th className="pb-2 font-medium">Last Login</th>
                  <th className="pb-2 font-medium text-right">Days Inactive</th>
                </tr>
              </thead>
              <tbody>
                {atRiskReps.map((rep) => (
                  <tr key={rep.name} className="border-b last:border-0">
                    <td className="py-2">{rep.name}</td>
                    <td className="py-2">{rep.lastLogin}</td>
                    <td className="py-2 text-right">{rep.days}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}