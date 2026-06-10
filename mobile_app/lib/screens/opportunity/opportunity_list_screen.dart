import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:one_cloud_app/services/api_client.dart';
class Opportunity {
  final String id;
  final String name;
  final String customer;
  final double amount;
  final String stage;
  final DateTime date;
  final String notes;

  const Opportunity({
    required this.id,
    required this.name,
    required this.customer,
    required this.amount,
    required this.stage,
    required this.date,
    this.notes = '',
  });
}

class OpportunityListScreen extends StatefulWidget {
  const OpportunityListScreen({super.key});
  @override
  State<OpportunityListScreen> createState() => _OpportunityListScreenState();
}

class _OpportunityListScreenState extends State<OpportunityListScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  static const _tabs = ['全部', '跟进中', '已转化', '已关闭'];

  List<Opportunity> _opportunities = [];
  bool _loading = false;

  List<Opportunity> get _filtered {
    if (_tabController.index == 0) return _opportunities;
    return _opportunities.where((o) => o.stage == _tabs[_tabController.index]).toList();
  }

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadData());
  }

  Future<void> _loadData() async {
    setState(() => _loading = true);
    final client = context.read<MultiBackendApiClient>();
    final res = await client.get<List>('/opportunities/');
    if (res.isSuccess && res.data != null) {
      _opportunities = res.data!.map((e) => Opportunity(
        id: e['id'].toString(),
        name: e['name'] ?? '',
        customer: e['customer_name'] ?? '',
        amount: (e['estimated_value'] ?? 0).toDouble(),
        stage: e['stage'] ?? '',
        date: DateTime.now(),
        notes: e['notes'] ?? '',
      )).toList();
    }
    setState(() => _loading = false);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  String _fmt(double amt) {
    if (amt >= 10000) return '¥${(amt / 10000).toStringAsFixed(1)}万';
    return '¥${amt.toStringAsFixed(0)}';
  }

  Future<void> _refresh() async {
    await _loadData();
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (_loading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    final list = _filtered;
    return Scaffold(
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
                        Icon(Icons.business_center, size: 64, color: Colors.grey[400]),
                        const SizedBox(height: 16),
                        Text('暂无商机', style: TextStyle(color: Colors.grey[600])),
                      ],
                    ),
                  )
                : RefreshIndicator(
                    onRefresh: _refresh,
                    child: ListView.builder(
                      padding: const EdgeInsets.all(12),
                      itemCount: list.length,
                      itemBuilder: (ctx, i) {
                        final o = list[i];
                        return Card(
                          child: ListTile(
                            contentPadding: const EdgeInsets.all(12),
                            title: Text(o.name, style: const TextStyle(fontWeight: FontWeight.w600)),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(o.customer),
                                const SizedBox(height: 4),
                                Row(
                                  children: [
                                    Text(_fmt(o.amount),
                                        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
                                    const SizedBox(width: 12),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: theme.colorScheme.primary.withValues(alpha: 0.1),
                                        borderRadius: BorderRadius.circular(4),
                                      ),
                                      child: Text(o.stage,
                                          style: TextStyle(fontSize: 11, color: theme.colorScheme.primary)),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                            trailing: Text('${o.date.month}/${o.date.day}',
                                style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                            onTap: () => Navigator.pushNamed(context, '/opportunity_detail', arguments: o.id),
                          ),
                        );
                      },
                    ),
                  ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => Navigator.pushNamed(context, '/opportunity_form'),
        child: const Icon(Icons.add),
      ),
    );
  }
}
