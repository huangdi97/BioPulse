export interface Paper {
  id: number
  title: string
  authors: string[]
  journal: string
  year: number
  citations: number
  keywords: string[]
  pmid: string
  abstract: string
  relevance: number
}

export interface PiProfile {
  id: number
  name: string
  institution: string
  title: string
  department: string
  h_index: number
  papers: number
  grants: string[]
  research_areas: string[]
  activity_score: number
}

export interface TargetTrend {
  month: string
  count: number
}

export interface Target {
  id: number
  name: string
  category: string
  paper_count: number
  trial_count: number
  growth: number
  trend_data: TargetTrend[]
}

export const papers: Paper[] = [
  { id: 1, title: '基于单细胞测序的肿瘤微环境异质性研究', authors: ['张伟', '李娟', '王强'], journal: 'Nature Medicine', year: 2025, citations: 128, keywords: ['单细胞测序', '肿瘤微环境', '异质性'], pmid: 'PM12345678', abstract: '利用单细胞RNA测序技术对肿瘤微环境中免疫细胞的异质性进行了系统分析，揭示了新型免疫检查点分子的表达特征，为免疫治疗提供了新的靶点方向。', relevance: 95 },
  { id: 2, title: 'PD-1抑制剂联合化疗在三阴性乳腺癌中的疗效预测生物标志物研究', authors: ['陈静', '刘洋'], journal: 'Cell', year: 2025, citations: 96, keywords: ['PD-1', '三阴性乳腺癌', '生物标志物'], pmid: 'PM12345679', abstract: '探索PD-1抑制剂联合化疗治疗三阴性乳腺癌的疗效预测生物标志物，发现肿瘤突变负荷和CD8+ T细胞浸润与治疗应答显著相关。', relevance: 92 },
  { id: 3, title: '基于深度学习的药物-靶点相互作用预测模型构建', authors: ['王磊', '赵敏', '周涛'], journal: 'Lancet Oncology', year: 2026, citations: 45, keywords: ['深度学习', '药物研发', '靶点预测'], pmid: 'PM12345680', abstract: '开发了一种基于图神经网络的新型药物-靶点相互作用预测模型，在基准数据集上AUC达0.94，显著优于现有方法。', relevance: 88 },
  { id: 4, title: 'CAR-T细胞治疗在复发难治性B细胞急性淋巴细胞白血病中的长期随访', authors: ['孙丽', '马超'], journal: 'New England Journal of Medicine', year: 2025, citations: 210, keywords: ['CAR-T', '白血病', '细胞治疗'], pmid: 'PM12345681', abstract: '对120例接受CAR-T细胞治疗的复发难治性B-ALL患者进行了中位36个月的随访，5年总生存率达48%。', relevance: 90 },
  { id: 5, title: '肠道菌群代谢物调控免疫检查点抑制剂疗效的机制研究', authors: ['黄明', '林芳', '吴强'], journal: 'Science', year: 2024, citations: 312, keywords: ['肠道菌群', '免疫检查点抑制剂', '代谢物'], pmid: 'PM12345682', abstract: '发现肠道菌群产生的短链脂肪酸通过调节树突状细胞功能增强PD-1抗体的抗肿瘤免疫应答。', relevance: 85 },
  { id: 6, title: '基于CRISPR筛选的肝癌新靶点发现及功能验证', authors: ['杨帆', '周杰'], journal: 'Nature Biotechnology', year: 2026, citations: 32, keywords: ['CRISPR', '肝癌', '靶点发现'], pmid: 'PM12345683', abstract: '通过全基因组CRISPR筛选技术鉴定出10个肝癌新候选靶点，并对其中FXR1基因进行了深入的体外功能验证。', relevance: 80 },
  { id: 7, title: '人工智能辅助的个性化用药方案在非小细胞肺癌中的应用', authors: ['郑涛', '许静', '高远'], journal: 'Journal of Clinical Oncology', year: 2025, citations: 67, keywords: ['人工智能', '个性化用药', '非小细胞肺癌'], pmid: 'PM12345684', abstract: '构建了基于多模态数据的AI辅助用药决策系统，在非小细胞肺癌患者中开展前瞻性验证，治疗有效率提升至68%。', relevance: 78 },
  { id: 8, title: '外泌体miRNA作为肿瘤早期诊断标志物的多中心临床研究', authors: ['罗琳', '何强'], journal: 'Cancer Discovery', year: 2024, citations: 156, keywords: ['外泌体', 'miRNA', '早期诊断'], pmid: 'PM12345685', abstract: '基于3000例样本的多中心研究，建立了基于血浆外泌体miRNA图谱的泛癌早期诊断模型，灵敏度达82%。', relevance: 75 },
  { id: 9, title: '新型PROTAC分子靶向降解KRAS G12C的抗肿瘤活性研究', authors: ['曹阳', '丁丽', '沈浩'], journal: 'Nature Chemical Biology', year: 2025, citations: 89, keywords: ['PROTAC', 'KRAS G12C', '靶向降解'], pmid: 'PM12345686', abstract: '设计合成了一类新型PROTAC分子，能够高效诱导KRAS G12C蛋白降解，在多种KRAS突变肿瘤模型中显示出显著抗肿瘤活性。', relevance: 93 },
  { id: 10, title: '肿瘤浸润淋巴细胞治疗在晚期黑色素瘤中的II期临床试验', authors: ['邓峰', '彭娟'], journal: 'Nature Medicine', year: 2024, citations: 178, keywords: ['TIL', '黑色素瘤', '细胞治疗'], pmid: 'PM12345687', abstract: 'II期临床试验结果显示，肿瘤浸润淋巴细胞治疗在晚期黑色素瘤患者中客观缓解率达到46%，中位无进展生存期8.5个月。', relevance: 82 },
  { id: 11, title: '基于类器官模型的个体化药物敏感性检测平台开发', authors: ['宋文', '范英', '傅杰'], journal: 'Cell Stem Cell', year: 2025, citations: 54, keywords: ['类器官', '药物敏感性', '精准医疗'], pmid: 'PM12345688', abstract: '建立了覆盖12种肿瘤类型的类器官生物样本库，开发了基于类器官的药物敏感性检测平台，预测临床疗效准确率达88%。', relevance: 72 },
  { id: 12, title: '长链非编码RNA在胶质母细胞瘤耐药中的作用机制', authors: ['唐亮', '冯婷'], journal: 'Cancer Cell', year: 2024, citations: 134, keywords: ['lncRNA', '胶质母细胞瘤', '耐药'], pmid: 'PM12345689', abstract: '发现LINC00922通过海绵吸附miR-128-3p调控PI3K/Akt通路，促进胶质母细胞瘤对替莫唑胺的耐药性。', relevance: 70 },
  { id: 13, title: 'mRNA疫苗联合免疫检查点抑制剂在实体瘤中的临床前研究', authors: ['程伟', '姜华', '潘琳'], journal: 'Nature Communications', year: 2026, citations: 28, keywords: ['mRNA疫苗', '免疫检查点抑制剂', '实体瘤'], pmid: 'PM12345690', abstract: '开发了编码肿瘤新抗原的mRNA疫苗，与PD-1抗体联用在多种实体瘤小鼠模型中实现了100%肿瘤消退。', relevance: 87 },
  { id: 14, title: '代谢重编程在肿瘤免疫逃逸中的功能及机制研究', authors: ['任浩', '夏雪'], journal: 'Molecular Cell', year: 2025, citations: 73, keywords: ['代谢重编程', '免疫逃逸', '肿瘤'], pmid: 'PM12345691', abstract: '揭示肿瘤细胞通过上调脂肪酸氧化代谢抑制CD8+ T细胞杀伤功能的分子机制，为代谢免疫联合治疗提供了新策略。', relevance: 76 },
  { id: 15, title: '基于真实世界数据的罕见肿瘤靶向治疗疗效评估', authors: ['韩冰', '石磊', '武静'], journal: 'JAMA Oncology', year: 2024, citations: 112, keywords: ['真实世界数据', '罕见肿瘤', '靶向治疗'], pmid: 'PM12345692', abstract: '利用全国多中心真实世界数据，评估了12种靶向药物在8类罕见肿瘤中的疗效和安全性，为临床用药提供了循证依据。', relevance: 68 },
]

export const piProfiles: PiProfile[] = [
  { id: 1, name: '陈志强', institution: '北京大学肿瘤医院', title: '主任医师', department: '肿瘤内科', h_index: 58, papers: 187, grants: ['国自然重点项目', '国家重点研发计划'], research_areas: ['肿瘤免疫治疗', '靶向治疗', '临床转化'], activity_score: 88 },
  { id: 2, name: '刘芳华', institution: '复旦大学附属中山医院', title: '教授', department: '心血管内科', h_index: 45, papers: 156, grants: ['国自然面上项目', '上海市科委项目'], research_areas: ['心血管药理学', '动脉粥样硬化', '脂质代谢'], activity_score: 76 },
  { id: 3, name: '王建国', institution: '中国医学科学院', title: '研究员', department: '免疫学', h_index: 62, papers: 203, grants: ['国家杰出青年基金', '国自然重大项目', '科技部863计划'], research_areas: ['免疫检查点', '细胞因子', '肿瘤免疫'], activity_score: 92 },
  { id: 4, name: '张明辉', institution: '上海交通大学医学院', title: '教授', department: '神经科学', h_index: 39, papers: 124, grants: ['国自然面上项目', '教育部重点实验室基金'], research_areas: ['神经退行性疾病', '药物递送', '血脑屏障'], activity_score: 65 },
  { id: 5, name: '李秀芝', institution: '北京协和医院', title: '主任医师', department: '内分泌科', h_index: 51, papers: 168, grants: ['国自然面上项目', '北京市自然科学基金'], research_areas: ['糖尿病', '代谢性疾病', '内分泌肿瘤'], activity_score: 71 },
  { id: 6, name: '赵伟峰', institution: '中山大学肿瘤防治中心', title: '研究员', department: '分子生物学', h_index: 55, papers: 179, grants: ['国家优秀青年基金', '国自然重点项目', '广东省科技计划'], research_areas: ['肿瘤基因组学', '表观遗传学', '精准医疗'], activity_score: 84 },
]

function makeTrend(base: number, variance: number): TargetTrend[] {
  const months = ['2025-04', '2025-05', '2025-06', '2025-07', '2025-08', '2025-09', '2025-10', '2025-11', '2025-12', '2026-01', '2026-02', '2026-03']
  return months.map((month, i) => ({
    month,
    count: Math.max(0, Math.round(base + Math.sin(i * 0.8) * variance + (Math.random() - 0.5) * variance * 0.4)),
  }))
}

export const targets: Target[] = [
  { id: 1, name: 'PD-1', category: '免疫检查点', paper_count: 18420, trial_count: 3820, growth: 12.5, trend_data: makeTrend(1500, 200) },
  { id: 2, name: 'HER2', category: '受体酪氨酸激酶', paper_count: 8650, trial_count: 1580, growth: 5.2, trend_data: makeTrend(720, 80) },
  { id: 3, name: 'EGFR', category: '受体酪氨酸激酶', paper_count: 12350, trial_count: 2450, growth: 3.8, trend_data: makeTrend(1030, 120) },
  { id: 4, name: 'CTLA-4', category: '免疫检查点', paper_count: 4520, trial_count: 890, growth: 8.1, trend_data: makeTrend(380, 60) },
  { id: 5, name: 'KRAS G12C', category: '信号转导', paper_count: 2890, trial_count: 520, growth: 35.6, trend_data: makeTrend(240, 70) },
  { id: 6, name: 'VEGF', category: '血管生成因子', paper_count: 9870, trial_count: 2100, growth: 2.1, trend_data: makeTrend(820, 90) },
  { id: 7, name: 'CD19', category: '免疫细胞表面抗原', paper_count: 3210, trial_count: 680, growth: 15.4, trend_data: makeTrend(270, 50) },
  { id: 8, name: 'BCMA', category: '免疫细胞表面抗原', paper_count: 1870, trial_count: 420, growth: 22.8, trend_data: makeTrend(160, 40) },
  { id: 9, name: 'ALK', category: '受体酪氨酸激酶', paper_count: 3450, trial_count: 750, growth: 6.7, trend_data: makeTrend(290, 45) },
  { id: 10, name: 'PARP1', category: 'DNA修复酶', paper_count: 5670, trial_count: 1120, growth: 18.3, trend_data: makeTrend(470, 85) },
]
