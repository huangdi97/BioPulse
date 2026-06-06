import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:one_cloud_app/models/visit.dart';
import 'package:one_cloud_app/services/database_service.dart';
import 'package:one_cloud_app/services/sync_service.dart';
import 'package:one_cloud_app/services/api_client.dart';
import 'package:one_cloud_app/screens/pharma/visit_form_screen.dart';

class VisitListScreen extends StatefulWidget {
  const VisitListScreen({super.key});

  @override
  State<VisitListScreen> createState() => _VisitListScreenState();
}

class _VisitListScreenState extends State<VisitListScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final List<Visit> _visits = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _tabController.addListener(() {
      if (!_tabController.indexIsChanging) _loadVisits();
    });
    _loadVisits();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadVisits() async {
    setState(() => _loading = true);
    try {
      final api = context.read<MultiBackendApiClient>();
      final response = await api
          .getClient('cloud')
          .get<Map<String, dynamic>>('/api/demo/team-ranks');
      if (response.isSuccess && response.data != null) {
        final ranks = response.data!['ranks'] as List<dynamic>? ?? [];
        final now = DateTime.now();
        _visits
          ..clear()
          ..addAll(ranks.map((r) => Visit(
                hcpName: r['name'] as String? ?? '',
                hospital: 'Demo医院',
                visitDate: now.toIso8601String(),
                visitType: 'routine',
                notes: '拜访${r['visits'] ?? 0}次 · 合规率${r['compliance_rate'] ?? 0}% · 成交${r['deals'] ?? 0}单',
                complianceStatus: ((r['compliance_rate'] as num?)?.toDouble() ?? 0) >= 80
                    ? 'compliant'
                    : 'non_compliant',
              )));
        if (mounted) setState(() => _loading = false);
        return;
      }
    } catch (_) {}
    final db = context.read<DatabaseService>();
    final all = await db.getVisits();
    final now = DateTime.now();
    _visits
      ..clear()
      ..addAll(all.where((v) {
        final date = DateTime.tryParse(v.visitDate);
        if (date == null) return false;
        switch (_tabController.index) {
          case 0:
            return date.year == now.year &&
                date.month == now.month &&
                date.day == now.day;
          case 1:
            final weekStart = now.subtract(Duration(days: now.weekday - 1));
            final weekEnd =
                weekStart.add(const Duration(days: 6, hours: 23, minutes: 59));
            return !date.isBefore(weekStart) && !date.isAfter(weekEnd);
          case 2:
            return date.year == now.year && date.month == now.month;
          default:
            return false;
        }
      }).toList());
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _onRefresh() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs.getString('backend_urls');
      String? baseUrl;
      if (saved != null) {
        final urls = Map<String, String>.from(jsonDecode(saved) as Map);
        baseUrl = urls['assistant'] ?? urls['sales_assistant'];
      }
      if (baseUrl != null) {
        await context.read<SyncService>().pullVisits(baseUrl);
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('同步服务暂不可用')),
        );
      }
    }
    await _loadVisits();
  }

  Color _complianceColor(String? status) {
    switch (status) {
      case 'compliant':
        return Colors.green;
      case 'non_compliant':
        return Colors.red;
      case 'pending_review':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  String _complianceLabel(String? status) {
    switch (status) {
      case 'compliant':
        return '合规';
      case 'non_compliant':
        return '违规';
      case 'pending_review':
        return '待审核';
      default:
        return '未检测';
    }
  }

  String _visitTypeLabel(String type) {
    switch (type) {
      case 'academic':
        return '学术拜访';
      case 'routine':
        return '日常拜访';
      case 'conference':
        return '学术会议';
      default:
        return type;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: Column(
        children: [
          TabBar(
            controller: _tabController,
            labelColor: theme.colorScheme.primary,
            unselectedLabelColor: Colors.grey,
            tabs: const [
              Tab(text: '今日'),
              Tab(text: '本周'),
              Tab(text: '本月'),
            ],
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _visits.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.event_busy,
                                size: 64, color: Colors.grey[400]),
                            const SizedBox(height: 16),
                            Text('暂无拜访记录',
                                style: TextStyle(color: Colors.grey[600])),
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _onRefresh,
                        child: ListView.builder(
                          padding: const EdgeInsets.all(12),
                          itemCount: _visits.length,
                          itemBuilder: (ctx, i) {
                            final v = _visits[i];
                            return Card(
                              child: ListTile(
                                contentPadding: const EdgeInsets.all(12),
                                leading: CircleAvatar(
                                  backgroundColor: _complianceColor(
                                          v.complianceStatus)
                                      .withValues(alpha: 0.15),
                                  child: Icon(Icons.person,
                                      color:
                                          _complianceColor(v.complianceStatus)),
                                ),
                                title: Text(v.hcpName,
                                    style:
                                        const TextStyle(fontWeight: FontWeight.w600)),
                                subtitle: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                        '${v.hospital}${v.department != null ? ' · ${v.department}' : ''}'),
                                    const SizedBox(height: 4),
                                    Row(
                                      children: [
                                        Icon(Icons.access_time,
                                            size: 14,
                                            color: Colors.grey[600]),
                                        const SizedBox(width: 4),
                                        Text(v.visitDate,
                                            style: TextStyle(
                                                fontSize: 12,
                                                color: Colors.grey[600])),
                                        const SizedBox(width: 12),
                                        Container(
                                          padding: const EdgeInsets.symmetric(
                                              horizontal: 6, vertical: 2),
                                          decoration: BoxDecoration(
                                            color: _complianceColor(
                                                    v.complianceStatus)
                                                .withValues(alpha: 0.1),
                                            borderRadius:
                                                BorderRadius.circular(4),
                                          ),
                                          child: Text(
                                            _complianceLabel(
                                                v.complianceStatus),
                                            style: TextStyle(
                                              fontSize: 11,
                                              color: _complianceColor(
                                                  v.complianceStatus),
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                                trailing: Chip(
                                  label: Text(
                                    _visitTypeLabel(v.visitType),
                                    style: const TextStyle(fontSize: 11),
                                  ),
                                  visualDensity: VisualDensity.compact,
                                ),
                                onTap: () async {
                                  await Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) =>
                                          VisitFormScreen(visit: v),
                                    ),
                                  );
                                  _loadVisits();
                                },
                              ),
                            );
                          },
                        ),
                      ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          await Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const VisitFormScreen()),
          );
          _loadVisits();
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}
