import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:biopulse_app/services/api_client.dart';

class AnalysisReportScreen extends StatefulWidget {
  const AnalysisReportScreen({super.key});

  @override
  State<AnalysisReportScreen> createState() => _AnalysisReportScreenState();
}

class _AnalysisReportScreenState extends State<AnalysisReportScreen> {
  Map<String, dynamic>? _report;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _loadFromApi();
  }

  Future<void> _loadFromApi() async {
    setState(() => _loading = true);
    try {
      final api = context.read<MultiBackendApiClient>();
      final id = ModalRoute.of(context)!.settings.arguments as String;
      final res = await api.getClient('sales_coach').get<Map>('/stats/report/');
      if (res.isSuccess && res.data != null) {
        _report = res.data as Map<String, dynamic>?;
      }
    } catch (_) {}
    setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    if (_report == null && _loading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    if (_report == null) return const Scaffold(body: Center(child: Text('加载失败')));
    final id = ModalRoute.of(context)!.settings.arguments as String;
    final data = _report!;
    final theme = Theme.of(context);
    final score = data['score'] as int;

    Widget _chip(String label, Color color) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        margin: const EdgeInsets.only(right: 8, bottom: 8),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Text(label, style: TextStyle(fontSize: 13, color: color)),
      );
    }

    return Scaffold(
      appBar: AppBar(title: Text(data['name'] as String)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  Text('综合评分',
                      style: TextStyle(
                          fontSize: 14, color: Colors.grey[600])),
                  const SizedBox(height: 8),
                  Text('$score',
                      style: TextStyle(
                          fontSize: 56,
                          fontWeight: FontWeight.bold,
                          color: score >= 80
                              ? Colors.green
                              : score >= 60
                                  ? Colors.orange
                                  : Colors.red)),
                  const SizedBox(height: 4),
                  Text(score >= 80
                      ? '优秀'
                      : score >= 60
                          ? '良好'
                          : '待提升',
                      style: TextStyle(
                          fontSize: 16,
                          color: Colors.grey[600])),
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
                  const Text('优势',
                      style: TextStyle(
                          fontWeight: FontWeight.w600, fontSize: 15)),
                  const SizedBox(height: 10),
                  Wrap(
                    children: (data['strengths'] as List<String>)
                        .map((s) => _chip(s, Colors.blue))
                        .toList(),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('待改进',
                      style: TextStyle(
                          fontWeight: FontWeight.w600, fontSize: 15)),
                  const SizedBox(height: 10),
                  Wrap(
                    children: (data['weaknesses'] as List<String>)
                        .map((s) => _chip(s, Colors.red))
                        .toList(),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('改进建议',
                      style: TextStyle(
                          fontWeight: FontWeight.w600, fontSize: 15)),
                  const SizedBox(height: 10),
                  ...(data['suggestions'] as List<String>).map(
                    (s) => Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('• ',
                              style: TextStyle(
                                  color: theme.colorScheme.primary,
                                  fontWeight: FontWeight.bold)),
                          Expanded(child: Text(s, style: const TextStyle(fontSize: 14))),
                        ],
                      ),
                    ),
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
