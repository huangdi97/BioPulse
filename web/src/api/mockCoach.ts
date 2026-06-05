export interface Scenario {
  id: number
  name: string
  description: string
  difficulty: '初级' | '中级' | '高级'
  category: '拜访' | '异议' | '合规' | '谈判' | '产品介绍'
  completed: boolean
  score: number
  duration: number
  tags: string[]
}

export interface TrainingRecord {
  id: number
  scenario_name: string
  date: string
  score: number
  duration: number
  weakness: string
  strength: string
}

export interface AbilityDimension {
  name: string
  score: number
  target: number
}

export interface AbilityAssessment {
  dimensions: AbilityDimension[]
  average: number
  suggestions: string[]
}

export const scenarios: Scenario[] = [
  {
    id: 1,
    name: '初访破冰',
    description: '第一次拜访陌生HCP，建立专业形象与信任基础',
    difficulty: '初级',
    category: '拜访',
    completed: false,
    score: 0,
    duration: 15,
    tags: ['拜访', '破冰', 'HCP'],
  },
  {
    id: 2,
    name: '异议处理',
    description: 'HCP质疑药品疗效，运用循证医学证据合理回应',
    difficulty: '中级',
    category: '异议',
    completed: true,
    score: 82,
    duration: 25,
    tags: ['异议', '沟通', '循证医学'],
  },
  {
    id: 3,
    name: '合规红线',
    description: '代表面临统方诱惑，坚守合规底线做出正确决策',
    difficulty: '高级',
    category: '合规',
    completed: false,
    score: 0,
    duration: 20,
    tags: ['合规', '统方', '职业道德'],
  },
  {
    id: 4,
    name: '价格谈判',
    description: '院长要求大幅降价，争取最优合作条件',
    difficulty: '中级',
    category: '谈判',
    completed: true,
    score: 73,
    duration: 30,
    tags: ['谈判', '价格', '院长'],
  },
  {
    id: 5,
    name: '产品介绍',
    description: '向科室主任系统介绍新药优势与临床证据',
    difficulty: '初级',
    category: '产品介绍',
    completed: false,
    score: 0,
    duration: 15,
    tags: ['产品', '科室主任', '介绍'],
  },
]

export const trainingRecords: TrainingRecord[] = [
  { id: 1, scenario_name: '异议处理', date: '2026-06-03', score: 82, duration: 25, weakness: '证据引用不够充分', strength: '回应态度专业' },
  { id: 2, scenario_name: '价格谈判', date: '2026-06-02', score: 73, duration: 30, weakness: '让步节奏过快', strength: '价格底线清晰' },
  { id: 3, scenario_name: '初访破冰', date: '2026-05-30', score: 91, duration: 15, weakness: '开场略显紧张', strength: '破冰自然流畅' },
  { id: 4, scenario_name: '产品介绍', date: '2026-05-28', score: 65, duration: 15, weakness: '数据记忆不准确', strength: '逻辑结构清晰' },
  { id: 5, scenario_name: '异议处理', date: '2026-05-25', score: 88, duration: 22, weakness: '忽略患者获益', strength: '引用文献恰当' },
  { id: 6, scenario_name: '合规红线', date: '2026-05-22', score: 95, duration: 20, weakness: '反应稍慢', strength: '最终决策正确' },
  { id: 7, scenario_name: '价格谈判', date: '2026-05-20', score: 58, duration: 28, weakness: '缺乏替代方案', strength: '态度坚决' },
  { id: 8, scenario_name: '初访破冰', date: '2026-05-18', score: 77, duration: 14, weakness: '产品信息不足', strength: '倾听能力好' },
  { id: 9, scenario_name: '产品介绍', date: '2026-05-15', score: 84, duration: 16, weakness: '互动不够', strength: '幻灯片熟练' },
  { id: 10, scenario_name: '合规红线', date: '2026-05-12', score: 69, duration: 22, weakness: '模棱两可', strength: '识别风险' },
]

export const abilityAssessment: AbilityAssessment = {
  dimensions: [
    { name: '产品知识', score: 78, target: 85 },
    { name: '沟通技巧', score: 85, target: 90 },
    { name: '异议处理', score: 72, target: 80 },
    { name: '合规意识', score: 90, target: 95 },
    { name: '谈判能力', score: 65, target: 80 },
  ],
  average: 78,
  suggestions: [
    '加强产品关键数据的记忆训练，提升产品知识维度',
    '学习SPIN销售提问技巧，提高异议处理深度',
    '模拟真实降价场景，掌握让步策略与替代方案',
    '强化合规红线的反应速度训练，缩短决策时间',
    '增加多角色扮演练习，提升沟通灵活性',
  ],
}
