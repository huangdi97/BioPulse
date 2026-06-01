import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:one_cloud_app/models/surgery.dart';
import 'package:one_cloud_app/services/database_service.dart';

class SurgeryFormScreen extends StatefulWidget {
  final Surgery? surgery;
  const SurgeryFormScreen({super.key, this.surgery});
  @override
  State<SurgeryFormScreen> createState() => _SurgeryFormScreenState();
}

class _SurgeryFormScreenState extends State<SurgeryFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _patientController = TextEditingController();
  final _hospitalController = TextEditingController();
  String _surgeryType = '骨科';
  DateTime _scheduledDate = DateTime.now();
  final List<Map<String, dynamic>> _checklistItems = [];
  bool _saving = false;

  static const _surgeryTypes = [
    '骨科', '普外科', '神经外科', '心胸外科', '泌尿外科',
    '妇产科', '眼科', '耳鼻喉科', '口腔科', '其他',
  ];

  @override
  void initState() {
    super.initState();
    if (widget.surgery != null) {
      final s = widget.surgery!;
      _patientController.text = s.patientName;
      _hospitalController.text = s.hospital;
      _surgeryType = s.surgeryType;
      final date = DateTime.tryParse(s.scheduledDate);
      if (date != null) _scheduledDate = date;
      if (s.prepChecklist != null && s.prepChecklist!.isNotEmpty) {
        final parsed = jsonDecode(s.prepChecklist!) as List;
        _checklistItems.addAll(parsed.cast<Map<String, dynamic>>());
      }
    }
  }

  @override
  void dispose() {
    _patientController.dispose();
    _hospitalController.dispose();
    super.dispose();
  }

  void _addChecklistItem() {
    setState(() {
      _checklistItems.add({
        'productName': '',
        'spec': '',
        'quantity': 1,
        'verified': false,
      });
    });
  }

  void _removeChecklistItem(int index) {
    setState(() => _checklistItems.removeAt(index));
  }

  Future<void> _pickDate() async {
    final d = await showDatePicker(
      context: context,
      initialDate: _scheduledDate,
      firstDate: DateTime(2020),
      lastDate: DateTime(2030),
    );
    if (d != null) setState(() => _scheduledDate = d);
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    final db = context.read<DatabaseService>();
    final surgery = Surgery(
      id: widget.surgery?.id,
      patientName: _patientController.text.trim(),
      hospital: _hospitalController.text.trim(),
      surgeryType: _surgeryType,
      scheduledDate: _scheduledDate.toIso8601String(),
      status: widget.surgery?.status ?? 'pending',
      prepChecklist: jsonEncode(_checklistItems),
      intraOpNotes: widget.surgery?.intraOpNotes,
      postOpReport: widget.surgery?.postOpReport,
    );
    if (widget.surgery?.id != null) {
      await db.updateSurgery(surgery);
    } else {
      await db.insertSurgery(surgery);
    }
    setState(() => _saving = false);
    if (mounted) Navigator.pop(context, true);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
          title: Text(widget.surgery != null ? '编辑手术' : '新建手术')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextFormField(
              controller: _patientController,
              decoration: const InputDecoration(labelText: '患者姓名'),
              validator: (v) =>
                  v == null || v.trim().isEmpty ? '请输入患者姓名' : null,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _hospitalController,
              decoration: const InputDecoration(labelText: '医院'),
              validator: (v) =>
                  v == null || v.trim().isEmpty ? '请输入医院' : null,
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _surgeryType,
              decoration: const InputDecoration(labelText: '手术类型'),
              items: _surgeryTypes
                  .map((t) =>
                      DropdownMenuItem(value: t, child: Text(t)))
                  .toList(),
              onChanged: (v) => setState(() => _surgeryType = v!),
            ),
            const SizedBox(height: 16),
            InkWell(
              onTap: _pickDate,
              child: InputDecorator(
                decoration: const InputDecoration(labelText: '预约日期'),
                child: Text(
                  '${_scheduledDate.year}-${_scheduledDate.month.toString().padLeft(2, '0')}-${_scheduledDate.day.toString().padLeft(2, '0')}',
                ),
              ),
            ),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('备货清单',
                    style: TextStyle(
                        fontWeight: FontWeight.w600, fontSize: 16)),
                TextButton.icon(
                  onPressed: _addChecklistItem,
                  icon: const Icon(Icons.add, size: 20),
                  label: const Text('添加'),
                ),
              ],
            ),
            ..._checklistItems.asMap().entries.map((entry) {
              final i = entry.key;
              final item = entry.value;
              return Card(
                key: ValueKey(i),
                margin: const EdgeInsets.only(bottom: 8),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              decoration: const InputDecoration(
                                  labelText: '产品名',
                                  isDense: true),
                              controller: TextEditingController(
                                  text: item['productName'] as String),
                              onChanged: (v) => item['productName'] = v,
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.close,
                                color: Colors.red, size: 20),
                            onPressed: () => _removeChecklistItem(i),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              decoration: const InputDecoration(
                                  labelText: '规格', isDense: true),
                              controller: TextEditingController(
                                  text: item['spec'] as String),
                              onChanged: (v) => item['spec'] = v,
                            ),
                          ),
                          const SizedBox(width: 12),
                          SizedBox(
                            width: 80,
                            child: TextField(
                              decoration: const InputDecoration(
                                  labelText: '数量',
                                  isDense: true),
                              keyboardType: TextInputType.number,
                              controller: TextEditingController(
                                  text: item['quantity'].toString()),
                              onChanged: (v) =>
                                  item['quantity'] = int.tryParse(v) ?? 1,
                            ),
                          ),
                          const SizedBox(width: 12),
                          FilterChip(
                            label: Text(item['verified'] == true
                                ? '已核验'
                                : '未核验'),
                            selected: item['verified'] == true,
                            onSelected: (v) =>
                                setState(() => item['verified'] = v),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              );
            }),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _saving ? null : _save,
              child: _saving
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white),
                    )
                  : const Text('保存'),
            ),
          ],
        ),
      ),
    );
  }
}
