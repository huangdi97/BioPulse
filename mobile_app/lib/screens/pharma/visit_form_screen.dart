import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:one_cloud_app/models/visit.dart';
import 'package:one_cloud_app/models/hcp.dart';
import 'package:one_cloud_app/models/compliance_result.dart';
import 'package:one_cloud_app/services/database_service.dart';

class VisitFormScreen extends StatefulWidget {
  final Visit? visit;
  const VisitFormScreen({super.key, this.visit});

  @override
  State<VisitFormScreen> createState() => _VisitFormScreenState();
}

class _VisitFormScreenState extends State<VisitFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _notesController = TextEditingController();
  HCP? _selectedHCP;
  DateTime _visitDate = DateTime.now();
  TimeOfDay _visitTime = TimeOfDay.now();
  String _visitType = 'academic';
  final List<String> _selectedProducts = [];
  bool _saving = false;

  static const _productOptions = [
    '产品A（降压药）',
    '产品B（降糖药）',
    '产品C（抗生素）',
    '产品D（抗病毒）',
    '产品E（心血管）',
  ];

  static const _visitTypes = ['academic', 'routine', 'conference'];
  static const _visitTypeLabels = {
    'academic': '学术拜访',
    'routine': '日常拜访',
    'conference': '学术会议',
  };

  static const _sensitiveWords = [
    '保证治愈', '一定有效', '最有效', '100%', '毫无副作用',
    '替代', '比XX好', '首选', '唯一',
  ];

  @override
  void initState() {
    super.initState();
    if (widget.visit != null) {
      final v = widget.visit!;
      _notesController.text = v.notes ?? '';
      _visitType = v.visitType;
      _selectedHCP = HCP(
        id: null,
        name: v.hcpName,
        hospital: v.hospital,
        department: v.department,
        createdAt: '',
      );
      final date = DateTime.tryParse(v.visitDate);
      if (date != null) {
        _visitDate = date;
        _visitTime = TimeOfDay.fromDateTime(date);
      }
      if (v.products != null && v.products!.isNotEmpty) {
        _selectedProducts
            .addAll(v.products!.split(',').map((e) => e.trim()).where((e) => e.isNotEmpty));
      }
    }
  }

  @override
  void dispose() {
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final d = await showDatePicker(
      context: context,
      initialDate: _visitDate,
      firstDate: DateTime(2020),
      lastDate: DateTime(2030),
    );
    if (d != null) setState(() => _visitDate = d);
  }

  Future<void> _pickTime() async {
    final t = await showTimePicker(
      context: context,
      initialTime: _visitTime,
    );
    if (t != null) setState(() => _visitTime = t);
  }

  Future<void> _searchHCP() async {
    final db = context.read<DatabaseService>();
    final result = await showSearch<HCP?>(
      context: context,
      delegate: _HCPSearchDelegate(db),
    );
    if (result != null) setState(() => _selectedHCP = result);
  }

  ComplianceResult _localComplianceCheck(String notes) {
    final violations = <String>[];
    final warnings = <String>[];
    for (final word in _sensitiveWords) {
      if (notes.contains(word)) {
        violations.add('备注中包含敏感词: "$word"');
      }
    }
    if (_selectedProducts.isEmpty) {
      warnings.add('未选择关联产品');
    }
    final score = violations.isEmpty ? (warnings.isEmpty ? 100 : 80) : 40;
    return ComplianceResult(
      passed: violations.isEmpty,
      violations: violations,
      warnings: warnings,
      riskLevel: violations.isNotEmpty ? 'high' : (warnings.isNotEmpty ? 'medium' : 'low'),
      score: score,
    );
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedHCP == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请选择HCP')),
      );
      return;
    }

    final db = context.read<DatabaseService>();
    final result = _localComplianceCheck(_notesController.text);
    if (!result.passed && mounted) {
      final proceed = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('合规检测提示'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('以下问题需要关注:'),
              const SizedBox(height: 8),
              ...result.violations
                  .map((v) => Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Row(
                          children: [
                            const Icon(Icons.error, color: Colors.red, size: 16),
                            const SizedBox(width: 4),
                            Expanded(child: Text(v, style: const TextStyle(fontSize: 13))),
                          ],
                        ),
                      )),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('返回修改'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('忽略并保存'),
            ),
          ],
        ),
      );
      if (proceed != true) return;
    }

    setState(() => _saving = true);

    final visitDate = DateTime(
      _visitDate.year,
      _visitDate.month,
      _visitDate.day,
      _visitTime.hour,
      _visitTime.minute,
    );

    final visit = Visit(
      id: widget.visit?.id,
      hcpName: _selectedHCP!.name,
      hospital: _selectedHCP!.hospital,
      department: _selectedHCP!.department,
      visitDate: visitDate.toIso8601String(),
      visitType: _visitType,
      status: widget.visit?.status ?? 'pending',
      notes: _notesController.text,
      complianceStatus: result.passed ? 'compliant' : 'non_compliant',
      products: _selectedProducts.join(', '),
    );
    if (widget.visit?.id != null) {
      await db.updateVisit(visit);
    } else {
      await db.insertVisit(visit);
      if (_selectedHCP!.id != null) {
        await db.updateHCPLastVisit(
          _selectedHCP!.id!,
          visitDate.toIso8601String(),
        );
      }
    }

    setState(() => _saving = false);
    if (mounted) Navigator.pop(context, true);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.visit != null ? '编辑拜访' : '新建拜访')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const Text('选择HCP', style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            InkWell(
              onTap: _searchHCP,
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey[400]!),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: _selectedHCP != null
                          ? Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(_selectedHCP!.name,
                                    style: const TextStyle(fontWeight: FontWeight.w500)),
                                Text(
                                  '${_selectedHCP!.hospital}${_selectedHCP!.department != null ? ' · ${_selectedHCP!.department}' : ''}',
                                  style:
                                      TextStyle(fontSize: 12, color: Colors.grey[600]),
                                ),
                              ],
                            )
                          : Text('点击搜索并选择HCP',
                              style: TextStyle(color: Colors.grey[500])),
                    ),
                    const Icon(Icons.search),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: InkWell(
                    onTap: _pickDate,
                    child: InputDecorator(
                      decoration: const InputDecoration(labelText: '日期'),
                      child: Text(
                        '${_visitDate.year}-${_visitDate.month.toString().padLeft(2, '0')}-${_visitDate.day.toString().padLeft(2, '0')}'),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: InkWell(
                    onTap: _pickTime,
                    child: InputDecorator(
                      decoration: const InputDecoration(labelText: '时间'),
                      child: Text(_visitTime.format(context)),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _visitType,
              decoration: const InputDecoration(labelText: '拜访类型'),
              items: _visitTypes
                  .map((t) => DropdownMenuItem(
                      value: t, child: Text(_visitTypeLabels[t]!)))
                  .toList(),
              onChanged: (v) => setState(() => _visitType = v!),
            ),
            const SizedBox(height: 16),
            const Text('关联产品', style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            ..._productOptions.map((p) => CheckboxListTile(
                  title: Text(p, style: const TextStyle(fontSize: 14)),
                  value: _selectedProducts.contains(p),
                  contentPadding: EdgeInsets.zero,
                  visualDensity: VisualDensity.compact,
                  controlAffinity: ListTileControlAffinity.leading,
                  onChanged: (checked) {
                    setState(() {
                      if (checked == true) {
                        _selectedProducts.add(p);
                      } else {
                        _selectedProducts.remove(p);
                      }
                    });
                  },
                )),
            const SizedBox(height: 16),
            TextFormField(
              controller: _notesController,
              decoration: const InputDecoration(
                labelText: '备注',
                alignLabelWithHint: true,
              ),
              maxLines: 4,
            ),
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

class _HCPSearchDelegate extends SearchDelegate<HCP?> {
  final DatabaseService db;
  _HCPSearchDelegate(this.db);

  @override
  List<Widget>? buildActions(BuildContext context) => [
        IconButton(
          icon: const Icon(Icons.clear),
          onPressed: () => query = '',
        ),
      ];

  @override
  Widget? buildLeading(BuildContext context) => IconButton(
        icon: const Icon(Icons.arrow_back),
        onPressed: () => close(context, null),
      );

  @override
  Widget buildResults(BuildContext context) => _buildList(context);

  @override
  Widget buildSuggestions(BuildContext context) => _buildList(context);

  Widget _buildList(BuildContext context) {
    if (query.isEmpty) {
      return Center(
        child: Text('输入姓名或医院搜索',
            style: TextStyle(color: Colors.grey[500])),
      );
    }
    return FutureBuilder<List<HCP>>(
      future: db.searchHCPs(query),
      builder: (ctx, snap) {
        if (!snap.hasData) {
          return const Center(child: CircularProgressIndicator());
        }
        final list = snap.data!;
        if (list.isEmpty) {
          return Center(
            child: Text('未找到匹配的HCP',
                style: TextStyle(color: Colors.grey[500])),
          );
        }
        return ListView.builder(
          itemCount: list.length,
          itemBuilder: (_, i) => ListTile(
            leading: const CircleAvatar(child: Icon(Icons.person)),
            title: Text(list[i].name),
            subtitle: Text(
                '${list[i].hospital}${list[i].department != null ? ' · ${list[i].department}' : ''}'),
            onTap: () => close(context, list[i]),
          ),
        );
      },
    );
  }
}
