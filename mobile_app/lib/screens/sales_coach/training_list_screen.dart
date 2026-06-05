import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:one_cloud_app/services/api_client.dart';

class TrainingRecord {
  final String id;
  final String name;
  final DateTime date;
  final double score;
  final String status;

  const TrainingRecord({
    required this.id,
    required this.name,
    required this.date,
    required this.score,
    required this.status,
  });
}

final List<TrainingRecord> mockTrainings = [
  TrainingRecord(id: '1', name: '关节镜手术话术演练', date: DateTime(2026, 6, 3), score: 85, status: '已完成'),
  TrainingRecord(id: '2', name: '骨科产品知识考核', date: DateTime(2026, 6, 2), score: 72, status: '已完成'),
  TrainingRecord(id: '3', name: '客户异议处理模拟', date: DateTime(2026, 6, 1), score: 0, status: '待分析'),
  TrainingRecord(id: '4', name: '手术跟台标准化流程', date: DateTime(2026, 5, 30), score: 91, status: '已完成'),
  TrainingRecord(id: '5', name: '新产品上市话术训练', date: DateTime(2026, 5, 28), score: 0, status: '待分析'),
  TrainingRecord(id: '6', name: '合规销售沟通技巧', date: DateTime(2026, 5, 25), score: 68, status: '全部'),
];

class TrainingListScreen extends StatefulWidget {
  const TrainingListScreen({super.key});
  @override
  State<TrainingListScreen> createState() => _TrainingListScreenState();
}

class _TrainingListScreenState extends State<TrainingListScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  static const _tabs = ['全部', '待分析', '已完成'];

  List<TrainingRecord> get _filtered {
    final all = mockTrainings;
    if (_tabController.index == 0) return all;
    if (_tabController.index == 1) {
      return all.where((t) => t.status == '待分析').toList();
    }
    return all.where((t) => t.status == '已完成').toList();
  }

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _tabController.addListener(() => setState(() {}));
    _loadFromApi();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _refresh() async {
    await Future.delayed(const Duration(milliseconds: 300));
    setState(() {});
  }

  Future<void> _loadFromApi() async {
    try {
      final api = context.read<MultiBackendApiClient>();
      await api.getClient('coach').get('/coach/training-sessions');
    } catch (_) {}
  }

  Color _statusColor(String status) {
    switch (status) {
      case '已完成':
        return Colors.green;
      case '待分析':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final list = _filtered;
    return Scaffold(
      appBar: AppBar(title: const Text('销售教练')),
      body: Column(
        children: [
          TabBar(
            controller: _tabController,
            labelColor: theme.colorScheme.primary,
            unselectedLabelColor: Colors.grey,
            tabs: _tabs.map((t) => Tab(text: t)).toList(),
          ),
          Expanded(
            child: list.isEmpty
                ? Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.mic, size: 64, color: Colors.grey[400]),
                        const SizedBox(height: 16),
                        Text('暂无训练记录', style: TextStyle(color: Colors.grey[600])),
                      ],
                    ),
                  )
                : RefreshIndicator(
                    onRefresh: _refresh,
                    child: ListView.builder(
                      padding: const EdgeInsets.all(12),
                      itemCount: list.length,
                      itemBuilder: (ctx, i) {
                        final t = list[i];
                        return Card(
                          child: ListTile(
                            contentPadding: const EdgeInsets.all(12),
                            title: Text(t.name,
                                style: const TextStyle(fontWeight: FontWeight.w600)),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const SizedBox(height: 4),
                                Row(
                                  children: [
                                    Text('${t.date.month}/${t.date.day}',
                                        style: TextStyle(
                                            fontSize: 13,
                                            color: Colors.grey[600])),
                                    const SizedBox(width: 12),
                                    Container(
                                      padding: const EdgeInsets.symmetric(
                                          horizontal: 6, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: _statusColor(t.status)
                                            .withValues(alpha: 0.1),
                                        borderRadius: BorderRadius.circular(4),
                                      ),
                                      child: Text(t.status,
                                          style: TextStyle(
                                              fontSize: 11,
                                              color: _statusColor(t.status))),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                            trailing: t.score > 0
                                ? Text('${t.score.toInt()}分',
                                    style: TextStyle(
                                        fontSize: 16,
                                        fontWeight: FontWeight.bold,
                                        color: theme.colorScheme.primary))
                                : null,
                            onTap: () => Navigator.pushNamed(
                                context, '/analysis_report',
                                arguments: t.id),
                          ),
                        );
                      },
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}
