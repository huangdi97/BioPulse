import type {
  KpiCard,
  VisitStat,
  TeamRank,
  ViolationItem,
  ResearchKpi,
  PiSource,
  ProductMatchStat,
} from "../types/dashboard"

function daysAgo(n: number): string {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString().slice(0, 10)
}

export const pharmaKpis: KpiCard[] = [
  { title: "本月拜访", value: 128, change: 12, icon: "ClipboardCheck", trend: "up" },
  { title: "合规率", value: "94.2%", change: 3.1, icon: "ShieldCheck", trend: "up" },
  { title: "活跃代表", value: 42, change: -2, icon: "Users", trend: "down" },
  { title: "成单率", value: "38%", change: 5, icon: "TrendingUp", trend: "up" },
]

export const visitTrends: VisitStat[] = Array.from({ length: 30 }, (_, i) => ({
  date: daysAgo(29 - i),
  count: Math.floor(Math.random() * 40) + 80,
  passRate: Number((90 + Math.random() * 9).toFixed(1)),
}))

export const teamRanks: TeamRank[] = [
  { name: "张明", visits: 28, complianceRate: 98.5, deals: 12 },
  { name: "李华", visits: 25, complianceRate: 96.2, deals: 10 },
  { name: "王芳", visits: 24, complianceRate: 97.8, deals: 9 },
  { name: "赵强", visits: 22, complianceRate: 92.1, deals: 8 },
  { name: "陈静", visits: 21, complianceRate: 95.4, deals: 7 },
  { name: "刘洋", visits: 19, complianceRate: 88.7, deals: 6 },
  { name: "周磊", visits: 18, complianceRate: 91.3, deals: 5 },
  { name: "吴婷", visits: 16, complianceRate: 94.6, deals: 4 },
]

export const violations: ViolationItem[] = [
  { id: 1, repName: "赵强", type: "统方", detail: "未按规定上传处方数据", severity: "high", date: daysAgo(1), status: "pending" },
  { id: 2, repName: "刘洋", type: "利益输送", detail: "向医生提供不当礼品", severity: "high", date: daysAgo(2), status: "pending" },
  { id: 3, repName: "王芳", type: "备案异常", detail: "拜访记录缺失3天", severity: "medium", date: daysAgo(3), status: "pending" },
  { id: 4, repName: "张明", type: "场所异常", detail: "非备案场所进行推广", severity: "medium", date: daysAgo(4), status: "resolved" },
  { id: 5, repName: "陈静", type: "统方", detail: "处方数据上传延迟超24h", severity: "low", date: daysAgo(5), status: "resolved" },
  { id: 6, repName: "李华", type: "利益输送", detail: "学术赞助未提前申报", severity: "medium", date: daysAgo(6), status: "resolved" },
  { id: 7, repName: "周磊", type: "备案异常", detail: "代表备案信息过期", severity: "low", date: daysAgo(7), status: "pending" },
  { id: 8, repName: "吴婷", type: "场所异常", detail: "在非授权科室开展活动", severity: "high", date: daysAgo(8), status: "pending" },
  { id: 9, repName: "赵强", type: "统方", detail: "数据篡改嫌疑", severity: "high", date: daysAgo(9), status: "pending" },
  { id: 10, repName: "刘洋", type: "利益输送", detail: "未备案的学术会议赞助", severity: "medium", date: daysAgo(10), status: "resolved" },
]

export const researchKpis: ResearchKpi[] = [
  { title: "PI线索", value: 86, change: 23, icon: "FlaskConical" },
  { title: "产品匹配率", value: "72%", change: 8, icon: "GitCompare" },
  { title: "报价中", value: 34, change: -5, icon: "FileText" },
  { title: "成单额", value: "286万", change: 15, icon: "DollarSign" },
]

export const piSources: PiSource[] = [
  { name: "张伟", institution: "北京大学第一医院", matches: 12, lastActivity: daysAgo(0) },
  { name: "李强", institution: "上海瑞金医院", matches: 9, lastActivity: daysAgo(1) },
  { name: "王丽", institution: "广州中山医院", matches: 7, lastActivity: daysAgo(2) },
  { name: "刘波", institution: "华西医院", matches: 6, lastActivity: daysAgo(3) },
  { name: "陈明", institution: "武汉同济医院", matches: 5, lastActivity: daysAgo(4) },
  { name: "杨芳", institution: "浙江大学附属医院", matches: 4, lastActivity: daysAgo(5) },
]

export const productMatchStats: ProductMatchStat[] = [
  { category: "肿瘤药物", total: 120, matched: 96, rate: 80 },
  { category: "心血管药", total: 85, matched: 68, rate: 80 },
  { category: "中枢神经", total: 60, matched: 42, rate: 70 },
  { category: "抗感染药", total: 45, matched: 27, rate: 60 },
]

export const complianceKpis: KpiCard[] = [
  { title: "本月检查", value: 842, change: 5, icon: "ClipboardList", trend: "up" },
  { title: "通过率", value: "94.2%", change: 1.8, icon: "ShieldCheck", trend: "up" },
  { title: "违规", value: 49, change: -8, icon: "AlertTriangle", trend: "down" },
  { title: "待处理", value: 12, change: -3, icon: "Clock", trend: "down" },
]
