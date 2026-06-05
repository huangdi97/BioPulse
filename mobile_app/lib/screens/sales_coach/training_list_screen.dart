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



class TrainingListScreen extends StatefulWidget {
  const TrainingListScreen({super.key});
  @override
  State<TrainingListScreen> createState() => _TrainingListScreenState();
}

class _TrainingListScreenState extends State<TrainingListScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<TrainingRecord> _trainings = [];
  bool _loading = false;

  static const _tabs = ['全部', '待分析', '已完成'];

  List<TrainingRecord> get _filtered {
    final all = _trainings;
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
    await _loadFromApi();
    setState(() {});
  }

  Future<void> _loadFromApi() async {
    setState(() => _loading = true);
    try {
      final api = context.read<MultiBackendApiClient>();
      final res = await api.getClient('sales_coach').get<List>('/scenarios');
      if (res.isSuccess && res.data != null) {
        _trainings = res.data!.map((e) => TrainingRecord(
          id: (e['id'] ?? '').toString(),
          name: e['name'] ?? '',
          date: DateTime.now(),
          score: (e['score'] ?? 0).toDouble(),
          status: e['status'] ?? '待分析',
        )).toList();
      }
    } catch (_) {}
    setState(() => _loading = false);
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
