import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:one_cloud_app/services/api_client.dart';

const _mockReports = {
  '1': {
    'name': '关节镜手术话术演练',
    'score': 85,
    'strengths': ['表达流畅', '专业术语准确', '逻辑清晰'],
    'weaknesses': ['时间控制不足', '客户提问响应慢'],
    'suggestions': [
      '建议练习时间控制在3分钟内，可使用计时器辅助训练',
      '针对常见客户提问提前准备标准应答话术',
      '多进行角色互换演练，提高临场应变能力',
    ],
  },
  '2': {
    'name': '骨科产品知识考核',
    'score': 72,
    'strengths': ['产品规格熟悉'],
    'weaknesses': ['竞品对比不充分', '适应症记忆模糊'],
    'suggestions': [
      '每周复习一次竞品对比表，重点关注差异化优势',
      '使用记忆卡片巩固适应症和禁忌症',
      '结合实际案例加深产品知识理解',
    ],
  },
  '3': {
    'name': '客户异议处理模拟',
    'score': 0,
    'strengths': [],
    'weaknesses': ['尚未评估'],
    'suggestions': ['请完成训练后查看分析报告'],
  },
};

class AnalysisReportScreen extends StatefulWidget {
  const AnalysisReportScreen({super.key});

  @override
  State<AnalysisReportScreen> createState() => _AnalysisReportScreenState();
}

class _AnalysisReportScreenState extends State<AnalysisReportScreen> {
  @override
  void initState() {
    super.initState();
    _loadFromApi();
  }

  Future<void> _loadFromApi() async {
    try {
      final api = context.read<MultiBackendApiClient>();
      await api.getClient('coach').get('/coach/analysis-report');
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    final id = ModalRoute.of(context)!.settings.arguments as String;
    final data = _mockReports[id]!;
    final theme = Theme.of(context);
    final score = data['score'] as int;

    Widget _chip(String label, Color color) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        margin: const EdgeInsets.only(right: 8, bottom: 8),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Text(label, style: TextStyle(fontSize: 13, color: color)),
      );
    }

    return Scaffold(
      appBar: AppBar(title: Text(data['name'] as String)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  Text('综合评分',
                      style: TextStyle(
                          fontSize: 14, color: Colors.grey[600])),
                  const SizedBox(height: 8),
                  Text('$score',
                      style: TextStyle(
                          fontSize: 56,
                          fontWeight: FontWeight.bold,
                          color: score >= 80
                              ? Colors.green
                              : score >= 60
                                  ? Colors.orange
                                  : Colors.red)),
                  const SizedBox(height: 4),
                  Text(score >= 80
                      ? '优秀'
                      : score >= 60
                          ? '良好'
                          : '待提升',
                      style: TextStyle(
                          fontSize: 16,
                          color: Colors.grey[600])),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('优势',
                      style: TextStyle(
                          fontWeight: FontWeight.w600, fontSize: 15)),
                  const SizedBox(height: 10),
                  Wrap(
                    children: (data['strengths'] as List<String>)
                        .map((s) => _chip(s, Colors.blue))
                        .toList(),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('待改进',
                      style: TextStyle(
                          fontWeight: FontWeight.w600, fontSize: 15)),
                  const SizedBox(height: 10),
                  Wrap(
                    children: (data['weaknesses'] as List<String>)
                        .map((s) => _chip(s, Colors.red))
                        .toList(),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('改进建议',
                      style: TextStyle(
                          fontWeight: FontWeight.w600, fontSize: 15)),
                  const SizedBox(height: 10),
                  ...(data['suggestions'] as List<String>).map(
                    (s) => Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('• ',
                              style: TextStyle(
                                  color: theme.colorScheme.primary,
                                  fontWeight: FontWeight.bold)),
                          Expanded(child: Text(s, style: const TextStyle(fontSize: 14))),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
