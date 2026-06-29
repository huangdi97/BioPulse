import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:biopulse_app/services/api_client.dart';
import 'package:biopulse_app/widgets/dialogue_panel.dart';

const Map<String, String> _agentDisplayNames = {
  'compliance_monitor': '合规监测',
  'anomaly_analysis': '异常分析',
  'opportunity_scanner': '商机扫描',
  'sales_suggestion': '销售策略',
  'sales_coach_analyst': '销售教练',
  'knowledge_worker': '知识维护',
};

class AgentInsightBar extends StatelessWidget {
  final String pageId;

  const AgentInsightBar({super.key, required this.pageId});

  void _openDialogue(BuildContext context, Map<String, dynamic> insight) {
    final agentKey = insight['agent_key'] as String? ?? '';
    final agentName = _agentDisplayNames[agentKey] ??
        insight['agent_name'] as String? ??
        '';
    final summary = insight['summary'] as String? ??
        insight['insight_text'] as String? ??
        '';
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => DialoguePanel(
        agentKey: agentKey,
        agentName: agentName,
        context: {'summary': summary},
        onClose: () => Navigator.of(context).pop(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final api = context.read<ApiClient>();
    return FutureBuilder<ApiResponse<List>>(
      future: api.get<List>('/api/v1/agent/insights',
          queryParameters: {'page': pageId}),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const SizedBox(
            height: 40,
            child: Center(child: CircularProgressIndicator()),
          );
        }
        if (!snapshot.hasData ||
            snapshot.data?.data == null ||
            (snapshot.data!.data as List).isEmpty) {
          return const SizedBox.shrink();
        }
        final insights = snapshot.data!.data as List;
        return Container(
          decoration: const BoxDecoration(
            border: Border(
              left: BorderSide(color: Colors.blue, width: 3),
            ),
          ),
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: insights.map<Widget>((insight) {
              final map = insight as Map<String, dynamic>;
              final agentName = _agentDisplayNames[map['agent_key']] ?? map['agent_key'] ?? '';
              final insightText = map['summary'] as String? ?? '';
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            agentName,
                            style:
                                const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          Text(insightText),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.help_outline),
                      tooltip: '追问',
                      onPressed: () => _openDialogue(context, map),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        );
      },
    );
  }
}