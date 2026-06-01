import type { Task } from '@/types'

export const mockTasks: Task[] = [
  {
    id: 1,
    title: '拜访张明华主任 — 讨论新药处方方案',
    description: '协和医院心内科，准备产品资料和临床数据',
    status: 'pending',
    dueDate: '2026-05-30',
    relatedHcpId: 1,
  },
  {
    id: 2,
    title: '拜访李雪琴主任 — 学术交流',
    description: '复旦大学附属中山医院心内科',
    status: 'pending',
    dueDate: '2026-05-30',
    relatedHcpId: 2,
  },
  {
    id: 3,
    title: '提交月度拜访总结报告',
    description: '将本月拜访记录整理汇总提交',
    status: 'pending',
    dueDate: '2026-05-31',
  },
  {
    id: 4,
    title: '拜访刘伟强主任 — 产品介绍',
    description: '协和医院消化内科，重点介绍消化产品线',
    status: 'pending',
    dueDate: '2026-05-30',
    relatedHcpId: 5,
  },
  {
    id: 5,
    title: '拜访吴佳慧主任 — 用药反馈收集',
    description: '中山三院神经内科，收集新药使用反馈',
    status: 'pending',
    dueDate: '2026-05-30',
    relatedHcpId: 9,
  },
  {
    id: 6,
    title: '更新HCP拜访记录系统',
    description: '将纸质记录录入系统',
    status: 'completed',
    dueDate: '2026-05-29',
  },
  {
    id: 7,
    title: '准备学术会议邀请函',
    description: '为下周区域性学术会议准备材料并邀请重点HCP',
    status: 'completed',
    dueDate: '2026-05-28',
  },
]
