import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:biopulse_app/services/api_client.dart';

class AgentSummaryCard extends StatelessWidget {
  final String title;
  final String agentKey;
  final String pageId;
  final String variant;

  const AgentSummaryCard({
    super.key,
    required this.title,
    required this.agentKey,
    required this.pageId,
    required this.variant,
  });

  Color _borderColor() {
    switch (variant) {
      case 'suggestion':
        return Colors.green;
      case 'pulse':
        return Colors.orange;
      default:
        return Colors.blue;
    }
  }

  @override
  Widget build(BuildContext context) {
    final api = context.read<ApiClient>();
    return FutureBuilder<ApiResponse<Map<String, dynamic>>>(
      future: api.get<Map<String, dynamic>>(
        '/api/v1/agent/insights',
        queryParameters: {'page': pageId},
      ),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    height: 16,
                    width: 200,
                    decoration: BoxDecoration(
                      color: Colors.grey.shade200,
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    height: 12,
                    width: double.infinity,
                    decoration: BoxDecoration(
                      color: Colors.grey.shade200,
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                ],
              ),
            ),
          );
        }

        if (!snapshot.hasData ||
            snapshot.data?.data == null ||
            !snapshot.data!.isSuccess) {
          return const SizedBox.shrink();
        }

        final body = snapshot.data!.data!;
        final summary = body['summary'] as String? ?? '';
        final details = body['details'] as Map<String, dynamic>?;

        final detailEntries = details != null
            ? details.entries.take(3).toList()
            : <MapEntry<String, dynamic>>[];

        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: Container(
            decoration: BoxDecoration(
              border: Border(
                left: BorderSide(color: _borderColor(), width: 4),
              ),
            ),
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                    ),
                    const Spacer(),
                    InkWell(
                      onTap: () {
                        // Dismiss handled by parent state
                      },
                      child: const Icon(
                        Icons.close,
                        size: 16,
                        color: Colors.grey,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  summary,
                  style: const TextStyle(
                    fontSize: 13,
                    color: Colors.black87,
                  ),
                ),
                if (detailEntries.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 16,
                    runSpacing: 4,
                    children: detailEntries.map((entry) {
                      return Text(
                        '${entry.key}: ${entry.value}',
                        style: const TextStyle(
                          fontSize: 12,
                          color: Colors.grey,
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ],
            ),
          ),
        );
      },
    );
  }
}