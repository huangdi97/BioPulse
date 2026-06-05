import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:one_cloud_app/models/compliance_result.dart';
import 'package:one_cloud_app/services/api_client.dart';

class ComplianceScreen extends StatefulWidget {
  const ComplianceScreen({super.key});

  @override
  State<ComplianceScreen> createState() => _ComplianceScreenState();
}

class _ComplianceScreenState extends State<ComplianceScreen> {
  final _controller = TextEditingController();
  ComplianceResult? _result;
  bool _checking = false;
  List<Map<String, dynamic>> _violations = [];
  bool _violationsLoading = true;

  @override
  void initState() {
    super.initState();
    _loadViolations();
  }

  Future<void> _loadViolations() async {
    try {
      final api = context.read<MultiBackendApiClient>();
      final response = await api
          .getClient('cloud')
          .get<Map<String, dynamic>>('/api/demo/violations');
      if (response.isSuccess && response.data != null) {
        final list = response.data!['violations'] as List<dynamic>? ?? [];
        _violations = list
            .map((v) => Map<String, dynamic>.from(v as Map))
            .toList();
      }
    } catch (_) {}
    if (mounted) setState(() => _violationsLoading = false);
  }

  static final _ruleSet = [
    _Rule(r'保证[治愈|有效|痊愈|康复]', '禁止使用保证性疗效承诺'),
    _Rule(r'一定有效', '禁止使用确定性疗效表述'),
    _Rule(r'[最|极|超]有效', '禁止使用绝对化疗效描述'),
    _Rule(r'100%', '禁止使用100%等绝对化数据'),
    _Rule(r'毫无副作用|无毒副作用|无任何副作用', '禁止声明无副作用（违反药品广告法）'),
    _Rule(r'替代[^。]*[药|治疗]', '谨慎使用"替代"相关表述'),
    _Rule(r'比\S+好|优于\S+', '谨慎使用对比性表述'),
    _Rule(r'首选|首推|唯一|最好|最佳', '禁止使用排他性宣传用语'),
    _Rule(r'免费[领|送|赠]|赠送|赠药', '禁止使用促销性表述（违反医药代表规范）'),
    _Rule(r'治愈率|有效率[^。]*[0-9]+%', '禁止引用未经审批的疗效数据'),
  ];

  ComplianceResult _check(String text) {
    if (text.trim().isEmpty) {
      return const ComplianceResult(
        passed: true,
        score: 100,
        riskLevel: 'low',
      );
    }

    final violations = <String>[];
    final warnings = <String>[];

    for (final rule in _ruleSet) {
      if (rule.pattern.hasMatch(text)) {
        final match = rule.pattern.firstMatch(text)!;
        final found = match.group(0) ?? '';
        violations.add('发现违规内容 "$found": ${rule.description}');
      }
    }

    if (text.length < 10) {
      warnings.add('输入内容过短，建议补充详细信息');
    }

    final score = violations.isEmpty
        ? (warnings.isEmpty ? 100 : 85)
        : (30 - violations.length * 10).clamp(0, 30);

    return ComplianceResult(
      passed: violations.isEmpty,
      violations: violations,
      warnings: warnings,
      riskLevel: violations.isNotEmpty
          ? 'high'
          : (warnings.isNotEmpty ? 'medium' : 'low'),
      score: score,
    );
  }

  void _runCheck() {
    setState(() => _checking = true);
    Future.delayed(const Duration(milliseconds: 500), () {
      if (mounted) {
        setState(() {
          _result = _check(_controller.text);
          _checking = false;
        });
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Color _riskColor(String level) {
    switch (level) {
      case 'high':
        return Colors.red;
      case 'medium':
        return Colors.orange;
      default:
        return Colors.green;
    }
  }

  String _riskLabel(String level) {
    switch (level) {
      case 'high':
        return '高风险';
      case 'medium':
        return '中风险';
      default:
        return '低风险';
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('合规文本检测',
                      style: TextStyle(
                          fontSize: 16, fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  Text(
                    '输入拜访记录、会议纪要或宣传文案进行合规检测',
                    style: TextStyle(color: Colors.grey[600], fontSize: 13),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _controller,
                    decoration: const InputDecoration(
                      hintText: '请输入需要检测的文本内容...',
                      alignLabelWithHint: true,
                    ),
                    maxLines: 6,
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: _checking ? null : _runCheck,
                      icon: _checking
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                  strokeWidth: 2, color: Colors.white),
                            )
                          : const Icon(Icons.verified),
                      label: Text(_checking ? '检测中...' : '开始检测'),
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (_result != null) ...[
            const SizedBox(height: 16),
            _buildResultCard(theme),
          ],
        ],
      ),
    );
  }

  Widget _buildResultCard(ThemeData theme) {
    final r = _result!;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  r.passed ? Icons.check_circle : Icons.cancel,
                  color: r.passed ? Colors.green : Colors.red,
                  size: 28,
                ),
                const SizedBox(width: 8),
                Text(
                  r.passed ? '检测通过' : '检测未通过',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: r.passed ? Colors.green : Colors.red,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                _resultBadge('评分', '${r.score}', r.score >= 80 ? Colors.green : (r.score >= 50 ? Colors.orange : Colors.red)),
                const SizedBox(width: 12),
                _resultBadge('风险', _riskLabel(r.riskLevel), _riskColor(r.riskLevel)),
              ],
            ),
            if (r.violations.isNotEmpty) ...[
              const Divider(),
              const Text('违规项', style: TextStyle(fontWeight: FontWeight.w600, color: Colors.red)),
              const SizedBox(height: 8),
              ...r.violations.map((v) => Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.error, color: Colors.red, size: 16),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(v, style: const TextStyle(fontSize: 13)),
                              const SizedBox(height: 2),
                              Text(
                                _suggestionFor(v),
                                style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  )),
            ],
            if (r.warnings.isNotEmpty) ...[
              const Divider(),
              const Text('警告项', style: TextStyle(fontWeight: FontWeight.w600, color: Colors.orange)),
              const SizedBox(height: 8),
              ...r.warnings.map((w) => Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Row(
                      children: [
                        const Icon(Icons.warning, color: Colors.orange, size: 16),
                        const SizedBox(width: 6),
                        Expanded(child: Text(w, style: const TextStyle(fontSize: 13))),
                      ],
                    ),
                  )),
            ],
          ],
        ),
      ),
    );
  }

  Widget _resultBadge(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          children: [
            Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
            Text(label, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
          ],
        ),
      ),
    );
  }

  String _suggestionFor(String violation) {
    if (violation.contains('保证')) return '建议: 使用"可能有助于"代替保证性用语';
    if (violation.contains('100%')) return '建议: 引用具体临床数据来源，避免绝对化表述';
    if (violation.contains('副作用')) return '建议: 改为"需在医生指导下使用"';
    if (violation.contains('替代')) return '建议: 使用"可作为治疗选择之一"';
    if (violation.contains('比') || violation.contains('优于')) return '建议: 避免直接比较，可引用客观临床研究数据';
    if (violation.contains('首选') || violation.contains('唯一') || violation.contains('最好') || violation.contains('最佳')) return '建议: 使用"可选择"、"可考虑"等中性表述';
    if (violation.contains('免费') || violation.contains('赠送') || violation.contains('赠药')) return '建议: 不得包含促销性内容';
    if (violation.contains('治愈率') || violation.contains('有效率')) return '建议: 仅使用国家药监局批准的说明书中的疗效数据';
    if (violation.contains('一定有效')) return '建议: 使用"临床研究表明可能有效"';
    return '建议: 修改相关表述以符合合规要求';
  }
}

class _Rule {
  final RegExp pattern;
  final String description;
  _Rule(String p, this.description) : pattern = RegExp(p);
}
