import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:one_cloud_app/services/api_client.dart';

class AgentInsightBar extends StatelessWidget {
  final String pageId;

  const AgentInsightBar({super.key, required this.pageId});

  @override
  Widget build(BuildContext context) {
    final api = context.read<ApiClient>();
    return FutureBuilder<ApiResponse<List>>(
      future: api.get<List>('/api/v1/agent/insights', queryParameters: {'page': pageId}),
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
              final agentName = map['agent_name'] as String? ?? '';
              final insightText = map['insight_text'] as String? ?? '';
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      agentName,
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    Text(insightText),
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