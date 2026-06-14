import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:biopulse_app/models/surgery.dart';
import 'package:biopulse_app/services/database_service.dart';
import 'package:biopulse_app/services/sync_service.dart';
import 'package:biopulse_app/theme/design_tokens.dart';
import 'package:biopulse_app/screens/surgery/scan_screen.dart';
import 'package:biopulse_app/screens/surgery/surgery_form_screen.dart';
import 'package:biopulse_app/screens/surgery/surgery_list_screen.dart';
import 'package:biopulse_app/screens/surgery/surgery_detail_screen.dart';

class SurgeryHomeScreen extends StatefulWidget {
  const SurgeryHomeScreen({super.key});
  @override
  State<SurgeryHomeScreen> createState() => _SurgeryHomeScreenState();
}

class _SurgeryHomeScreenState extends State<SurgeryHomeScreen> {
  final List<Surgery> _todaySurgeries = [];
  bool _loading = true;
  int _pendingCount = 0;
  final _scrollController = ScrollController();
  bool _showScrollToTop = false;

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
    _scrollController.addListener(() {
      final show = _scrollController.offset > 300;
      if (show != _showScrollToTop) setState(() => _showScrollToTop = show);
    });
    _loadData();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() => _loading = true);
    final db = context.read<DatabaseService>();
    final sync = context.read<SyncService>();
    final all = await db.getSurgeries();
    final now = DateTime.now();
    final prefix = '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
    _todaySurgeries..clear()..addAll(all.where((s) => s.scheduledDate.startsWith(prefix)).take(5));
    _pendingCount = await sync.getPendingCount();
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _handleSync() async {
    final sync = context.read<SyncService>();
    await sync.syncPending();
    _pendingCount = await sync.getPendingCount();
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final dateStr = '${now.year}年${now.month}月${now.day}日';

    return Scaffold(
      appBar: AppBar(
        flexibleSpace: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(colors: [DesignTokens.brand, DesignTokens.brandHover]),
          ),
        ),
        title: const Text('跟台助手', style: TextStyle(color: DesignTokens.textInverse, fontWeight: FontWeight.bold)),
        actions: [
          if (_pendingCount > 0)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: Chip(
                label: Text('$_pendingCount', style: const TextStyle(color: Colors.white, fontSize: 11)),
                backgroundColor: Colors.white24,
                visualDensity: VisualDensity.compact,
              ),
            ),
        ],
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        child: ListView(
          controller: _scrollController,
          padding: const EdgeInsets.only(bottom: 16),
          children: [
            Container(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
              decoration: const BoxDecoration(
                gradient: LinearGradient(colors: [DesignTokens.brand, DesignTokens.brandHover]),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('欢迎使用跟台助手', style: TextStyle(color: DesignTokens.textInverse.withValues(alpha: 0.8), fontSize: 14)),
                  const SizedBox(height: 4),
                  Text(dateStr, style: TextStyle(color: DesignTokens.textInverse.withValues(alpha: 0.7), fontSize: 13)),
                ],
              ),
            ),
            SizedBox(
              height: 100,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                children: [
                  _buildActionCard(Icons.qr_code_scanner, '扫码', DesignTokens.modePass, () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ScanScreen()))),
                  _buildActionCard(Icons.add_circle_outline, '新建手术', DesignTokens.modePharma, () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SurgeryFormScreen()))),
                  _buildActionCard(Icons.calendar_month, '查看日程', DesignTokens.modeWarn, () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SurgeryListScreen()))),
                  _buildActionCard(Icons.offline_pin, '离线缓存', DesignTokens.modeResearch, null, badge: _todaySurgeries.length.toString()),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text('今日手术', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            ),
            if (_loading)
              const Padding(padding: EdgeInsets.all(32), child: Center(child: CircularProgressIndicator()))
            else if (_todaySurgeries.isEmpty)
              Center(
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  const SizedBox(height: 32),
                  Icon(Icons.local_hospital, size: 64, color: Colors.grey[400]),
                  const SizedBox(height: 16),
                  Text('今日暂无手术', style: TextStyle(color: Colors.grey[600])),
                ]),
              )
            else
              ..._todaySurgeries.map(_buildSurgeryCard),
            Container(
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(color: DesignTokens.brandLight, borderRadius: BorderRadius.circular(DesignTokens.radiusLg)),
              child: Row(
                children: [
                  Icon(Icons.sync, color: DesignTokens.brand, size: 20),
                  const SizedBox(width: 8),
                  Expanded(child: Text('待同步 $_pendingCount 条记录', style: TextStyle(color: DesignTokens.textSecondary))),
                  TextButton(onPressed: _handleSync, child: const Text('立即同步')),
                ],
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: _showScrollToTop
          ? FloatingActionButton.small(
              onPressed: () => _scrollController.animateTo(0, duration: const Duration(milliseconds: 300), curve: Curves.easeOut),
              child: const Icon(Icons.arrow_upward),
            )
          : null,
    );
  }

  Widget _buildSurgeryCard(Surgery s) {
    final color = _statusColors[s.status] ?? Colors.grey;
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: ListTile(
        contentPadding: const EdgeInsets.all(12),
        leading: CircleAvatar(
          backgroundColor: color.withValues(alpha: 0.15),
          child: Icon(Icons.medical_services, color: color),
        ),
        title: Text(s.patientName, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(s.hospital),
            const SizedBox(height: 4),
            Row(children: [
              Icon(Icons.access_time, size: 14, color: Colors.grey[600]),
              const SizedBox(width: 4),
              Text(_formatTime(s.scheduledDate), style: TextStyle(fontSize: 12, color: Colors.grey[600])),
              const SizedBox(width: 12),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(color: color.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(4)),
                child: Text(_statusLabels[s.status] ?? s.status, style: TextStyle(fontSize: 11, color: color)),
              ),
            ]),
          ],
        ),
        trailing: Chip(label: Text(s.surgeryType, style: const TextStyle(fontSize: 11)), visualDensity: VisualDensity.compact),
        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => SurgeryDetailScreen(surgery: s))),
      ),
    );
  }

  Widget _buildActionCard(IconData icon, String label, Color color, VoidCallback? onTap, {String? badge}) {
    return Padding(
      padding: const EdgeInsets.only(right: 12),
      child: Material(
        color: DesignTokens.surfaceCard,
        borderRadius: BorderRadius.circular(DesignTokens.radiusLg),
        elevation: 1,
        child: InkWell(
          borderRadius: BorderRadius.circular(DesignTokens.radiusLg),
          onTap: onTap,
          child: SizedBox(
            width: 80,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Stack(children: [
                  Icon(icon, size: 32, color: color),
                  if (badge != null)
                    Positioned(
                      right: -8, top: -8,
                      child: Container(
                        padding: const EdgeInsets.all(4),
                        decoration: const BoxDecoration(color: DesignTokens.error, shape: BoxShape.circle),
                        child: Text(badge!, style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                      ),
                    ),
                ]),
                const SizedBox(height: 6),
                Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
              ],
            ),
          ),
        ),
      ),
    );
  }

  String _formatTime(String dateStr) {
    final d = DateTime.tryParse(dateStr);
    if (d == null) return dateStr;
    return '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
  }
}
