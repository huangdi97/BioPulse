import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:one_cloud_app/models/surgery.dart';
import 'package:one_cloud_app/services/database_service.dart';
import 'package:one_cloud_app/screens/surgery/scan_screen.dart';

class SurgeryDetailScreen extends StatefulWidget {
  final Surgery surgery;
  const SurgeryDetailScreen({super.key, required this.surgery});
  @override
  State<SurgeryDetailScreen> createState() => _SurgeryDetailScreenState();
}

class _SurgeryDetailScreenState extends State<SurgeryDetailScreen> {
  late Surgery _surgery;
  final _notesController = TextEditingController();
  bool _loading = false;

  static const _statusOrder = ['pre_op', 'in_op', 'post_op', 'completed'];
  static const _statusLabels = {
    'pre_op': '术前',
    'in_op': '术中',
    'post_op': '术后',
    'completed': '完成',
  };

  @override
  void initState() {
    super.initState();
    _surgery = widget.surgery;
    _notesController.text = _surgery.intraOpNotes ?? '';
  }

  @override
  void dispose() {
    _notesController.dispose();
    super.dispose();
  }

  int _currentStatusIndex() {
    final idx = _statusOrder.indexOf(_surgery.status);
    return idx >= 0 ? idx : -1;
  }

  Future<void> _advanceStatus() async {
    final currentIdx = _currentStatusIndex();
    if (currentIdx < 0 || currentIdx >= _statusOrder.length - 1) {
      return;
    }
    final nextStatus = _statusOrder[currentIdx + 1];
    final db = context.read<DatabaseService>();
    _surgery = _surgery.copyWith(status: nextStatus);
    await db.updateSurgery(_surgery);
    setState(() {});
  }

  Future<void> _verifyItem(int index) async {
    final items = _getChecklist();
    if (index >= items.length) return;
    items[index]['verified'] = true;
    final db = context.read<DatabaseService>();
    _surgery = _surgery.copyWith(prepChecklist: jsonEncode(items));
    await db.updateSurgery(_surgery);
    setState(() {});
  }

  List<Map<String, dynamic>> _getChecklist() {
    if (_surgery.prepChecklist == null ||
        _surgery.prepChecklist!.isEmpty) {
      return [];
    }
    final parsed = jsonDecode(_surgery.prepChecklist!);
    return (parsed as List).cast<Map<String, dynamic>>();
  }

  Future<void> _saveNotes() async {
    final db = context.read<DatabaseService>();
    _surgery = _surgery.copyWith(intraOpNotes: _notesController.text);
    await db.updateSurgery(_surgery);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('术中记录已保存')),
      );
    }
  }

  Future<void> _generateReport() async {
    setState(() => _loading = true);
    final report = '术后报告 - ${_surgery.patientName}\n'
        '手术类型: ${_surgery.surgeryType}\n'
        '医院: ${_surgery.hospital}\n'
        '日期: ${_surgery.scheduledDate}\n'
        '术中记录: ${_notesController.text}\n'
        '状态: ${_surgery.status}';
    final db = context.read<DatabaseService>();
    _surgery = _surgery.copyWith(postOpReport: report);
    await db.updateSurgery(_surgery);
    setState(() => _loading = false);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('报告已生成')),
      );
    }
  }

  Future<void> _openScanner() async {
    final result = await Navigator.push<String>(
      context,
      MaterialPageRoute(builder: (_) => const ScanScreen()),
    );
    if (result != null && result.isNotEmpty) {
      _notesController.text += '\n[扫码] $result';
      await _saveNotes();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final checklist = _getChecklist();
    final allVerified = checklist.isNotEmpty &&
        checklist.every((item) => item['verified'] == true);

    return Scaffold(
      appBar: AppBar(title: Text('手术详情 - ${_surgery.patientName}')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(_surgery.patientName,
                      style: theme.textTheme.titleLarge
                          ?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 4),
                  Text('${_surgery.hospital} · ${_surgery.surgeryType}'),
                  Text(_surgery.scheduledDate,
                      style: TextStyle(color: Colors.grey[600])),
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
                  const Text('手术进度',
                      style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 12),
                  Row(
                    children: List.generate(_statusOrder.length, (i) {
                      final status = _statusOrder[i];
                      final isActive = i <= _currentStatusIndex();
                      final isCurrent = i == _currentStatusIndex();
                      return Expanded(
                        child: GestureDetector(
                          onTap: isCurrent ? _advanceStatus : null,
                          child: Column(
                            children: [
                              Container(
                                width: 32,
                                height: 32,
                                decoration: BoxDecoration(
                                  color: isActive
                                      ? theme.colorScheme.primary
                                      : Colors.grey[300],
                                  shape: BoxShape.circle,
                                ),
                                child: Icon(
                                  isCurrent ? Icons.arrow_forward : Icons.check,
                                  size: 16,
                                  color: Colors.white,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(_statusLabels[status]!,
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight:
                                        isCurrent ? FontWeight.bold : null,
                                    color: isActive
                                        ? theme.colorScheme.primary
                                        : Colors.grey,
                                  )),
                            ],
                          ),
                        ),
                      );
                    }),
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
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('备货清单',
                          style: TextStyle(fontWeight: FontWeight.w600)),
                      if (allVerified)
                        Chip(
                          avatar: const Icon(Icons.check_circle,
                              size: 16, color: Colors.green),
                          label: const Text('全部已核验',
                              style: TextStyle(fontSize: 11)),
                          visualDensity: VisualDensity.compact,
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  if (checklist.isEmpty)
                    Text('暂无备货清单',
                        style: TextStyle(color: Colors.grey[500]))
                  else
                    ...checklist.asMap().entries.map((entry) {
                      final i = entry.key;
                      final item = entry.value;
                      final verified = item['verified'] == true;
                      return ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(
                          verified
                              ? Icons.check_circle
                              : Icons.radio_button_unchecked,
                          color: verified ? Colors.green : Colors.grey,
                        ),
                        title: Text(item['productName'] as String? ?? ''),
                        subtitle: Text(
                            '${item['spec']} × ${item['quantity']}'),
                        trailing: verified
                            ? null
                            : TextButton(
                                onPressed: () => _verifyItem(i),
                                child: const Text('核验'),
                              ),
                      );
                    }),
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
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('术中记录',
                          style: TextStyle(fontWeight: FontWeight.w600)),
                      Row(
                        children: [
                          IconButton(
                            icon: const Icon(Icons.qr_code_scanner,
                                size: 20),
                            tooltip: '扫码',
                            onPressed: _openScanner,
                          ),
                          IconButton(
                            icon: const Icon(Icons.camera_alt, size: 20),
                            tooltip: '拍照',
                            onPressed: () async {
                              final result = await Navigator.push<String>(
                                context,
                                MaterialPageRoute(
                                    builder: (_) => const ScanScreen()),
                              );
                              if (result != null) {
                                _notesController.text += '\n[照片] $result';
                                await _saveNotes();
                              }
                            },
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _notesController,
                    maxLines: 5,
                    decoration: const InputDecoration(
                      hintText: '记录手术过程中的重要信息...',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton.icon(
                      onPressed: _saveNotes,
                      icon: const Icon(Icons.save, size: 18),
                      label: const Text('保存记录'),
                    ),
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
                  const Text('术后报告',
                      style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  if (_surgery.postOpReport != null)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.grey[100],
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(_surgery.postOpReport!),
                    )
                  else
                    Text('尚未生成报告',
                        style: TextStyle(color: Colors.grey[500])),
                  const SizedBox(height: 12),
                  ElevatedButton.icon(
                    onPressed: _loading ? null : _generateReport,
                    icon: _loading
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                                strokeWidth: 2),
                          )
                        : const Icon(Icons.description),
                    label: const Text('生成报告'),
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
