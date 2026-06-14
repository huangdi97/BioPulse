import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:biopulse_app/services/api_client.dart';

class Recommendation {
  final String id;
  final String category;
  final String title;
  final String description;
  final bool unread;

  const Recommendation({
    required this.id,
    required this.category,
    required this.title,
    required this.description,
    this.unread = true,
  });
}


class RecommendationScreen extends StatefulWidget {
  const RecommendationScreen({super.key});
  @override
  State<RecommendationScreen> createState() => _RecommendationScreenState();
}

class _RecommendationScreenState extends State<RecommendationScreen> {
  late List<Recommendation> _data;

  @override
  void initState() {
    super.initState();
    _data = [];
    _loadFromApi();
  }

  Future<void> _loadFromApi() async {
    try {
      final api = context.read<MultiBackendApiClient>();
      final res = await api.getClient('sales_coach').get<List>('/scenarios/recommendations');
      if (res.isSuccess && res.data != null) {
        _data = res.data!.map((e) => Recommendation(
          id: (e['id'] ?? '').toString(),
          category: e['category'] ?? '',
          title: e['title'] ?? '',
          description: e['description'] ?? '',
          unread: e['unread'] ?? true,
        )).toList();
        if (mounted) setState(() {});
      }
    } catch (_) {}
  }

  void _markRead(String id) {
    setState(() {
      _data = _data.map((r) => r.id == id ? Recommendation(id: r.id, category: r.category, title: r.title, description: r.description, unread: false) : r).toList();
    });
  }

  Color _categoryColor(String cat) {
    switch (cat) {
      case '话术':
        return Colors.blue;
      case '产品知识':
        return Colors.teal;
      case '销售技巧':
        return Colors.purple;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('推荐内容')),
      body: _data.isEmpty
          ? Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.lightbulb_outline, size: 64, color: Colors.grey[400]),
                  const SizedBox(height: 16),
                  Text('暂无推荐', style: TextStyle(color: Colors.grey[600])),
                ],
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: _data.length,
              itemBuilder: (ctx, i) {
                final r = _data[i];
                return Card(
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: _categoryColor(r.category)
                                    .withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(r.category,
                                  style: TextStyle(
                                      fontSize: 11,
                                      color: _categoryColor(r.category))),
                            ),
                            const SizedBox(width: 8),
                            if (r.unread)
                              Container(
                                width: 8,
                                height: 8,
                                decoration: const BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: Colors.orange,
                                ),
                              ),
                            const Spacer(),
                            if (r.unread)
                              TextButton(
                                onPressed: () => _markRead(r.id),
                                child: const Text('标为已读',
                                    style: TextStyle(fontSize: 12)),
                              ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          r.title,
                          style: TextStyle(
                            fontWeight:
                                r.unread ? FontWeight.bold : FontWeight.w500,
                            fontSize: 15,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(r.description,
                            style: TextStyle(
                                fontSize: 13, color: Colors.grey[700])),
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }
}
