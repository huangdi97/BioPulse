import 'package:flutter/material.dart';

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

final List<Opportunity> mockOpportunities = [
  Opportunity(id: '1', name: '关节镜设备采购', customer: '市第一人民医院', amount: 120000, stage: '跟进中', date: DateTime(2026, 6, 1), notes: '已提交初步方案'),
  Opportunity(id: '2', name: '骨科植入物供应', customer: '市中心医院', amount: 85000, stage: '跟进中', date: DateTime(2026, 5, 28), notes: '第二次拜访完成'),
  Opportunity(id: '3', name: '手术导航系统', customer: '省立医院', amount: 300000, stage: '已转化', date: DateTime(2026, 5, 20), notes: '合同已签署'),
  Opportunity(id: '4', name: '康复设备租赁', customer: '康复医院', amount: 45000, stage: '已关闭', date: DateTime(2026, 5, 15), notes: '客户预算不足'),
  Opportunity(id: '5', name: 'CT影像系统升级', customer: '人民医院', amount: 200000, stage: '跟进中', date: DateTime(2026, 6, 3), notes: '技术交流已完成'),
];

class OpportunityListScreen extends StatefulWidget {
  const OpportunityListScreen({super.key});
  @override
  State<OpportunityListScreen> createState() => _OpportunityListScreenState();
}

class _OpportunityListScreenState extends State<OpportunityListScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  static const _tabs = ['全部', '跟进中', '已转化', '已关闭'];

  List<Opportunity> get _filtered {
    if (_tabController.index == 0) return mockOpportunities;
    return mockOpportunities.where((o) => o.stage == _tabs[_tabController.index]).toList();
  }

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
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
    await Future.delayed(const Duration(milliseconds: 300));
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
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
