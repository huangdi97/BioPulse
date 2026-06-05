import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:one_cloud_app/models/surgery.dart';
import 'package:one_cloud_app/services/database_service.dart';
import 'package:one_cloud_app/services/sync_service.dart';
import 'package:one_cloud_app/screens/surgery/surgery_form_screen.dart';

class SurgeryListScreen extends StatefulWidget {
  const SurgeryListScreen({super.key});
  @override
  State<SurgeryListScreen> createState() => _SurgeryListScreenState();
}

class _SurgeryListScreenState extends State<SurgeryListScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final List<Surgery> _surgeries = [];
  bool _loading = true;

  static const _statusColors = {
    'pending': Colors.grey,
    'pre_op': Colors.blue,
    'in_op': Colors.orange,
    'post_op': Colors.purple,
    'completed': Colors.green,
  };

  static const _statusLabels = {
    'pending': '待手术',
    'pre_op': '术前',
    'in_op': '术中',
    'post_op': '术后',
    'completed': '已完成',
  };

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _tabController.addListener(() {
      if (!_tabController.indexIsChanging) _loadSurgeries();
    });
    _loadSurgeries();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadSurgeries() async {
    setState(() => _loading = true);
    final db = context.read<DatabaseService>();
    final all = await db.getSurgeries();
    final now = DateTime.now();
    _surgeries
      ..clear()
      ..addAll(all.where((s) {
        final date = DateTime.tryParse(s.scheduledDate);
        if (date == null) return _tabController.index == 2;
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
          default:
            return true;
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
        await context.read<SyncService>().pullSurgeries(baseUrl);
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('同步服务暂不可用')),
        );
      }
    }
    await _loadSurgeries();
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
              Tab(text: '全部'),
            ],
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _surgeries.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.local_hospital,
                                size: 64, color: Colors.grey[400]),
                            const SizedBox(height: 16),
                            Text('暂无手术记录',
                                style: TextStyle(color: Colors.grey[600])),
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _onRefresh,
                        child: ListView.builder(
                          padding: const EdgeInsets.all(12),
                          itemCount: _surgeries.length,
                          itemBuilder: (ctx, i) {
                            final s = _surgeries[i];
                            final color = _statusColors[s.status] ?? Colors.grey;
                            return Card(
                              child: ListTile(
                                contentPadding: const EdgeInsets.all(12),
                                leading: CircleAvatar(
                                  backgroundColor: color.withValues(alpha: 0.15),
                                  child: Icon(Icons.medical_services,
                                      color: color),
                                ),
                                title: Text(s.patientName,
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w600)),
                                subtitle: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(s.hospital),
                                    const SizedBox(height: 4),
                                    Row(
                                      children: [
                                        Icon(Icons.access_time,
                                            size: 14,
                                            color: Colors.grey[600]),
                                        const SizedBox(width: 4),
                                        Text(s.scheduledDate,
                                            style: TextStyle(
                                                fontSize: 12,
                                                color: Colors.grey[600])),
                                        const SizedBox(width: 12),
                                        Container(
                                          padding: const EdgeInsets.symmetric(
                                              horizontal: 6, vertical: 2),
                                          decoration: BoxDecoration(
                                            color: color.withValues(alpha: 0.1),
                                            borderRadius:
                                                BorderRadius.circular(4),
                                          ),
                                          child: Text(
                                            _statusLabels[s.status] ?? s.status,
                                            style: TextStyle(
                                              fontSize: 11,
                                              color: color,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                                trailing: Chip(
                                  label: Text(s.surgeryType,
                                      style: const TextStyle(fontSize: 11)),
                                  visualDensity: VisualDensity.compact,
                                ),
                                onTap: () async {
                                  await Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) =>
                                          SurgeryFormScreen(surgery: s),
                                    ),
                                  );
                                  _loadSurgeries();
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
            MaterialPageRoute(
                builder: (_) => const SurgeryFormScreen()),
          );
          _loadSurgeries();
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}
