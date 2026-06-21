import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:biopulse_app/services/api_client.dart';
import 'package:biopulse_app/widgets/agent_insight_bar.dart';



class OpportunityDetailScreen extends StatefulWidget {
  const OpportunityDetailScreen({super.key});

  @override
  State<OpportunityDetailScreen> createState() => _OpportunityDetailScreenState();
}

class _OpportunityDetailScreenState extends State<OpportunityDetailScreen> {
  Map<String, dynamic>? _detail;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadData());
  }

  Future<void> _loadData() async {
    setState(() => _loading = true);
    final client = context.read<MultiBackendApiClient>();
    final id = ModalRoute.of(context)!.settings.arguments as String;
    final res = await client.get<Map>('/opportunities/$id');
    if (res.isSuccess && res.data != null) {
      setState(() => _detail = res.data as Map<String, dynamic>?);
    }
    setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    final id = ModalRoute.of(context)!.settings.arguments as String;
    final data = _detail;
    if (data == null) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    final theme = Theme.of(context);

    void snack(String msg) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));

    return Scaffold(
      appBar: AppBar(title: Text(data['name']!)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const AgentInsightBar(pageId: 'mobile_opp_detail'),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(data['name']!, style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  _row('客户', data['customer']!),
                  _row('金额', data['amount']!),
                  _row('阶段', data['stage']!),
                  _row('日期', data['date']!),
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
                  const Text('备注', style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  Text(data['notes']!, style: TextStyle(color: Colors.grey[700])),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              Expanded(child: ElevatedButton.icon(onPressed: () => snack('已记录跟进'), icon: const Icon(Icons.follow_the_signs), label: const Text('跟进'))),
              const SizedBox(width: 8),
              Expanded(child: ElevatedButton.icon(onPressed: () => snack('已标记为转化'), icon: const Icon(Icons.check_circle), label: const Text('转化'))),
              const SizedBox(width: 8),
              Expanded(child: ElevatedButton.icon(onPressed: () => snack('已关闭'), icon: const Icon(Icons.cancel), label: const Text('关闭'))),
            ],
          ),
        ],
      ),
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          SizedBox(width: 60, child: Text(label, style: TextStyle(color: Colors.grey[600]))),
          Expanded(child: Text(value, style: const TextStyle(fontWeight: FontWeight.w500))),
        ],
      ),
    );
  }
}
