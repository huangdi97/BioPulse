import 'package:flutter/material.dart';

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

final List<Recommendation> mockRecommendations = [
  Recommendation(
    id: '1',
    category: '话术',
    title: '关节镜销售开场白话术优化',
    description: '根据最新客户反馈，建议在开场白中加入成功案例数据，提升客户信任度。',
    unread: true,
  ),
  Recommendation(
    id: '2',
    category: '产品知识',
    title: '新一代骨科螺钉技术要点',
    description: '掌握新型可吸收螺钉的材料特性、适应症及与竞品的核心差异。',
    unread: true,
  ),
  Recommendation(
    id: '3',
    category: '销售技巧',
    title: '价格异议处理三步法',
    description: '面对客户价格质疑时，使用「认同-价值重塑-对比」的话术框架有效应对。',
    unread: false,
  ),
  Recommendation(
    id: '4',
    category: '话术',
    title: '术后回访标准话术',
    description: '规范化术后回访流程，提升客户满意度和复购率。',
    unread: true,
  ),
  Recommendation(
    id: '5',
    category: '产品知识',
    title: '竞品对比速查表更新',
    description: 'Q2季度竞品价格及参数更新，请及时同步最新数据。',
    unread: false,
  ),
];

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
    _data = mockRecommendations.map((r) => r).toList();
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
