import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:biopulse_app/models/hcp.dart';
import 'package:biopulse_app/models/visit.dart';
import 'package:biopulse_app/services/database_service.dart';
import 'package:biopulse_app/screens/pharma/visit_form_screen.dart';
import 'package:biopulse_app/widgets/agent_summary_card.dart';
import 'package:biopulse_app/widgets/agent_insight_bar.dart';

class HcpDetailScreen extends StatefulWidget {
  final int hcpId;
  const HcpDetailScreen({super.key, required this.hcpId});

  @override
  State<HcpDetailScreen> createState() => _HcpDetailScreenState();
}

class _HcpDetailScreenState extends State<HcpDetailScreen> {
  HCP? _hcp;
  List<Visit> _visits = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _loading = true);
    final db = context.read<DatabaseService>();
    final hcp = await db.getHCP(widget.hcpId);
    if (hcp != null) {
      final visits = await db.getVisitsByHCP(hcp.name);
      if (mounted) setState(() { _hcp = hcp; _visits = visits; _loading = false; });
    } else {
      if (mounted) setState(() => _loading = false);
    }
  }

  Map<String, int> _complianceStats() {
    int compliant = 0, nonCompliant = 0, pending = 0;
    for (final v in _visits) {
      switch (v.complianceStatus) {
        case 'compliant': compliant++; break;
        case 'non_compliant': nonCompliant++; break;
        default: pending++;
      }
    }
    return {'compliant': compliant, 'non_compliant': nonCompliant, 'pending': pending};
  }

  String _visitTypeLabel(String type) {
    switch (type) {
      case 'academic': return '学术拜访';
      case 'routine': return '日常拜访';
      case 'conference': return '学术会议';
      default: return type;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (_loading) return Scaffold(appBar: AppBar(title: const Text('HCP详情')), body: const Center(child: CircularProgressIndicator()));
    if (_hcp == null) return Scaffold(appBar: AppBar(title: const Text('HCP详情')), body: const Center(child: Text('未找到HCP')));

    final h = _hcp!;
    final stats = _complianceStats();

    return Scaffold(
      appBar: AppBar(
        title: Text(h.name),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: () => _showEditDialog(h),
          ),
        ],
      ),
      body: Column(
        children: [
          AgentSummaryCard(
            title: '情报摘要',
            agentKey: 'knowledge_worker',
            pageId: 'mobile_hcp_detail',
            variant: 'summary',
          ),
          const AgentInsightBar(pageId: 'mobile_hcp_detail'),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 28,
                        backgroundColor: theme.colorScheme.primary.withValues(alpha: 0.1),
                        child: Text(h.name[0].toUpperCase(),
                            style: TextStyle(fontSize: 24, color: theme.colorScheme.primary, fontWeight: FontWeight.bold)),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(h.name, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                            if (h.title != null) Text(h.title!, style: TextStyle(color: Colors.grey[600])),
                          ],
                        ),
                      ),
                      if (h.isActive)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(color: Colors.green[50], borderRadius: BorderRadius.circular(12)),
                          child: const Text('在职', style: TextStyle(color: Colors.green, fontSize: 12)),
                        ),
                    ],
                  ),
                  const Divider(),
                  _infoRow(Icons.business, '医院', h.hospital),
                  if (h.department != null) _infoRow(Icons.local_hospital, '科室', h.department!),
                  if (h.title != null) _infoRow(Icons.badge, '职称', h.title!),
                  if (h.phone != null) _infoRow(Icons.phone, '电话', h.phone!),
                  if (h.email != null) _infoRow(Icons.email, '邮箱', h.email!),
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
                  const Text('合规统计', style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      _statBadge(Colors.green, '合规', stats['compliant']!),
                      const SizedBox(width: 12),
                      _statBadge(Colors.red, '违规', stats['non_compliant']!),
                      const SizedBox(width: 12),
                      _statBadge(Colors.orange, '待审核', stats['pending']!),
                      const SizedBox(width: 12),
                      _statBadge(Colors.blue, '总次数', _visits.length),
                    ],
                  ),
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
                  const Text('拜访历史', style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  if (_visits.isEmpty)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 24),
                      child: Center(child: Text('暂无拜访记录', style: TextStyle(color: Colors.grey[500]))),
                    )
                  else
                    ..._visits.map((v) => ListTile(
                          contentPadding: EdgeInsets.zero,
                          leading: CircleAvatar(
                            radius: 18,
                            child: Text(_visitTypeLabel(v.visitType)[0], style: const TextStyle(fontSize: 12)),
                          ),
                          title: Text(_visitTypeLabel(v.visitType), style: const TextStyle(fontSize: 14)),
                          subtitle: Text(v.visitDate, style: const TextStyle(fontSize: 12)),
                          trailing: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: v.complianceStatus == 'compliant'
                                  ? Colors.green[50]
                                  : v.complianceStatus == 'non_compliant'
                                      ? Colors.red[50]
                                      : Colors.grey[100],
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              v.complianceStatus == 'compliant'
                                  ? '合规'
                                  : v.complianceStatus == 'non_compliant'
                                      ? '违规'
                                      : '待审核',
                              style: TextStyle(
                                fontSize: 11,
                                color: v.complianceStatus == 'compliant'
                                    ? Colors.green
                                    : v.complianceStatus == 'non_compliant'
                                        ? Colors.red
                                        : Colors.grey,
                              ),
                            ),
                          ),
                          onTap: () async {
                            await Navigator.push(
                              context,
                              MaterialPageRoute(builder: (_) => VisitFormScreen(visit: v)),
                            );
                            _loadData();
                          },
                        )),
                ],
              ),
            ),
          ),
          if (h.tags.isNotEmpty) ...[
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('标签', style: TextStyle(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: h.tags
                          .map((t) => Chip(
                                label: Text(t, style: const TextStyle(fontSize: 12)),
                                visualDensity: VisualDensity.compact,
                              ))
                          .toList(),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    ),
  ],
  ),
);
  }

  Widget _infoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(icon, size: 16, color: Colors.grey[600]),
          const SizedBox(width: 8),
          Text('$label: ', style: TextStyle(color: Colors.grey[600], fontSize: 14)),
          Text(value, style: const TextStyle(fontSize: 14)),
        ],
      ),
    );
  }

  Widget _statBadge(Color color, String label, int count) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          children: [
            Text('$count', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
            Text(label, style: TextStyle(fontSize: 11, color: Colors.grey[600])),
          ],
        ),
      ),
    );
  }

  void _showEditDialog(HCP h) {
    final nameCtl = TextEditingController(text: h.name);
    final hospCtl = TextEditingController(text: h.hospital);
    final deptCtl = TextEditingController(text: h.department ?? '');
    final titleCtl = TextEditingController(text: h.title ?? '');
    final phoneCtl = TextEditingController(text: h.phone ?? '');
    final emailCtl = TextEditingController(text: h.email ?? '');

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('编辑HCP'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: nameCtl, decoration: const InputDecoration(labelText: '姓名')),
              TextField(controller: hospCtl, decoration: const InputDecoration(labelText: '医院')),
              TextField(controller: deptCtl, decoration: const InputDecoration(labelText: '科室')),
              TextField(controller: titleCtl, decoration: const InputDecoration(labelText: '职称')),
              TextField(controller: phoneCtl, decoration: const InputDecoration(labelText: '电话')),
              TextField(controller: emailCtl, decoration: const InputDecoration(labelText: '邮箱')),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('取消')),
          ElevatedButton(
            onPressed: () async {
              final db = context.read<DatabaseService>();
              await db.updateHCP(h.copyWith(
                name: nameCtl.text.trim(),
                hospital: hospCtl.text.trim(),
                department: deptCtl.text.trim().isEmpty ? null : deptCtl.text.trim(),
                title: titleCtl.text.trim().isEmpty ? null : titleCtl.text.trim(),
                phone: phoneCtl.text.trim().isEmpty ? null : phoneCtl.text.trim(),
                email: emailCtl.text.trim().isEmpty ? null : emailCtl.text.trim(),
              ));
              if (ctx.mounted) Navigator.pop(ctx);
              _loadData();
            },
            child: const Text('保存'),
          ),
        ],
      ),
    );
  }
}
