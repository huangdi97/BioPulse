import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:biopulse_app/models/hcp.dart';
import 'package:biopulse_app/services/database_service.dart';
import 'package:biopulse_app/services/sync_service.dart';
import 'package:biopulse_app/services/api_client.dart';
import 'package:biopulse_app/screens/pharma/hcp_detail_screen.dart';

class HcpListScreen extends StatefulWidget {
  const HcpListScreen({super.key});

  @override
  State<HcpListScreen> createState() => _HcpListScreenState();
}

class _HcpListScreenState extends State<HcpListScreen> {
  final _searchController = TextEditingController();
  List<HCP> _allHCPs = [];
  List<HCP> _filteredHCPs = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadHCPs();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadHCPs() async {
    setState(() => _loading = true);
    try {
      final api = context.read<MultiBackendApiClient>();
      final response = await api
          .getClient('cloud')
          .get<Map<String, dynamic>>('/api/demo/team-ranks');
      if (response.isSuccess && response.data != null) {
        final ranks = response.data!['ranks'] as List<dynamic>? ?? [];
        _allHCPs = ranks.map((r) => HCP(
              name: r['name'] as String? ?? '',
              hospital: 'Demo医院',
              department: '待确认',
              title: '拜访${r['visits'] ?? 0}次 · 合规${r['compliance_rate'] ?? 0}% · 成交${r['deals'] ?? 0}单',
              createdAt: DateTime.now().toIso8601String(),
            )).toList();
        _applyFilter();
        if (mounted) setState(() => _loading = false);
        return;
      }
    } catch (_) {}
    final db = context.read<DatabaseService>();
    _allHCPs = await db.getHCPs();
    _applyFilter();
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
        await context.read<SyncService>().pullHcps(baseUrl);
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('同步服务暂不可用')),
        );
      }
    }
    await _loadHCPs();
  }

  void _applyFilter() {
    final q = _searchController.text.trim().toLowerCase();
    setState(() {
      _filteredHCPs = q.isEmpty
          ? List.from(_allHCPs)
          : _allHCPs.where((h) {
              return h.name.toLowerCase().contains(q) ||
                  h.hospital.toLowerCase().contains(q);
            }).toList();
    });
  }

  Future<void> _showAddDialog() async {
    final nameCtl = TextEditingController();
    final hospCtl = TextEditingController();
    final deptCtl = TextEditingController();
    final titleCtl = TextEditingController();
    final phoneCtl = TextEditingController();
    final emailCtl = TextEditingController();

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('添加HCP'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: nameCtl, decoration: const InputDecoration(labelText: '姓名', hintText: '必填')),
              TextField(controller: hospCtl, decoration: const InputDecoration(labelText: '医院', hintText: '必填')),
              TextField(controller: deptCtl, decoration: const InputDecoration(labelText: '科室')),
              TextField(controller: titleCtl, decoration: const InputDecoration(labelText: '职称')),
              TextField(controller: phoneCtl, decoration: const InputDecoration(labelText: '电话')),
              TextField(controller: emailCtl, decoration: const InputDecoration(labelText: '邮箱')),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('取消')),
          ElevatedButton(
            onPressed: () {
              if (nameCtl.text.trim().isEmpty || hospCtl.text.trim().isEmpty) {
                ScaffoldMessenger.of(ctx).showSnackBar(
                  const SnackBar(content: Text('姓名和医院为必填项')),
                );
                return;
              }
              Navigator.pop(ctx, true);
            },
            child: const Text('保存'),
          ),
        ],
      ),
    );

    if (saved == true && mounted) {
      final db = context.read<DatabaseService>();
      await db.insertHCP(HCP(
        name: nameCtl.text.trim(),
        hospital: hospCtl.text.trim(),
        department: deptCtl.text.trim().isEmpty ? null : deptCtl.text.trim(),
        title: titleCtl.text.trim().isEmpty ? null : titleCtl.text.trim(),
        phone: phoneCtl.text.trim().isEmpty ? null : phoneCtl.text.trim(),
        email: emailCtl.text.trim().isEmpty ? null : emailCtl.text.trim(),
        createdAt: DateTime.now().toIso8601String(),
      ));
      _loadHCPs();
    }

    nameCtl.dispose();
    hospCtl.dispose();
    deptCtl.dispose();
    titleCtl.dispose();
    phoneCtl.dispose();
    emailCtl.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 8, 12, 4),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: '搜索姓名或医院',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchController.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _searchController.clear();
                          _applyFilter();
                        },
                      )
                    : null,
              ),
              onChanged: (_) => _applyFilter(),
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _filteredHCPs.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.people_outline,
                                size: 64, color: Colors.grey[400]),
                            const SizedBox(height: 16),
                            Text('暂无HCP数据',
                                style: TextStyle(color: Colors.grey[600])),
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _onRefresh,
                        child: ListView.builder(
                          padding: const EdgeInsets.all(12),
                          itemCount: _filteredHCPs.length,
                          itemBuilder: (ctx, i) {
                            final h = _filteredHCPs[i];
                            return Card(
                              child: ListTile(
                                leading: CircleAvatar(
                                  backgroundColor: theme.colorScheme.primary
                                      .withValues(alpha: 0.1),
                                  child: Text(
                                    h.name.isNotEmpty
                                        ? h.name[0].toUpperCase()
                                        : '?',
                                    style: TextStyle(
                                      color: theme.colorScheme.primary,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                                title: Text(h.name,
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w600)),
                                subtitle: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                        '${h.hospital}${h.department != null ? ' · ${h.department}' : ''}'),
                                    if (h.title != null)
                                      Text(h.title!,
                                          style: TextStyle(
                                              fontSize: 12,
                                              color: Colors.grey[600])),
                                    if (h.lastVisitDate != null)
                                      Text(
                                        '最近拜访: ${h.lastVisitDate!.substring(0, 10)}',
                                        style: TextStyle(
                                            fontSize: 11,
                                            color: Colors.grey[500]),
                                      ),
                                  ],
                                ),
                                trailing: const Icon(Icons.chevron_right),
                                onTap: () async {
                                  await Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) =>
                                          HcpDetailScreen(hcpId: h.id!),
                                    ),
                                  );
                                  _loadHCPs();
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
        onPressed: _showAddDialog,
        child: const Icon(Icons.person_add),
      ),
    );
  }
}
