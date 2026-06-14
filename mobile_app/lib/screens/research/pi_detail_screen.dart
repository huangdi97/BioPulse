import 'package:flutter/material.dart';
import 'package:biopulse_app/models/pi_profile.dart';
import 'package:biopulse_app/screens/research/product_matching_screen.dart';

class PIDetailScreen extends StatelessWidget {
  final PIProfile profile;
  const PIDetailScreen({super.key, required this.profile});

  static const _topProducts = [
    {'name': '靶向免疫抑制剂-PD1', 'match': 92, 'spec': '100mg/瓶'},
    {'name': '肿瘤微环境调节剂-TME1', 'match': 88, 'spec': '50mg/片'},
    {'name': 'VEGF单克隆抗体', 'match': 85, 'spec': '400mg/支'},
  ];

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final areas = profile.researchAreas.isNotEmpty
        ? profile.researchAreas.split(',')
        : <String>[];

    return Scaffold(
      appBar: AppBar(title: Text(profile.name)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 32,
                    child: Text(profile.name.isNotEmpty
                        ? profile.name[0]
                        : '?'),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(profile.name,
                            style: theme.textTheme.titleLarge
                                ?.copyWith(fontWeight: FontWeight.bold)),
                        const SizedBox(height: 4),
                        Text(profile.institution,
                            style: TextStyle(color: Colors.grey[600])),
                        if (profile.activeYears.isNotEmpty)
                          Text('活跃年份: ${profile.activeYears}',
                              style: TextStyle(
                                  fontSize: 12, color: Colors.grey[500])),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _statItem('论文', '${profile.papersCount}'),
                  _statItem('H指数', '${profile.hIndex}'),
                  _statItem('活跃', profile.activeYears.isNotEmpty
                      ? profile.activeYears.split('-').first
                      : '-'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          if (areas.isNotEmpty)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('研究领域',
                        style: TextStyle(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: areas
                          .map((a) => Chip(
                                label: Text(a.trim(),
                                    style: const TextStyle(fontSize: 12)),
                                visualDensity: VisualDensity.compact,
                              ))
                          .toList(),
                    ),
                  ],
                ),
              ),
            ),
          if (profile.bio != null && profile.bio!.isNotEmpty) ...[
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('简介',
                        style: TextStyle(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 8),
                    Text(profile.bio!),
                  ],
                ),
              ),
            ),
          ],
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('匹配产品推荐',
                          style: TextStyle(fontWeight: FontWeight.w600)),
                      TextButton(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) =>
                                  ProductMatchingScreen(profile: profile),
                            ),
                          );
                        },
                        child: const Text('查看全部'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  ..._topProducts.map((p) => ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: CircleAvatar(
                          backgroundColor:
                              theme.colorScheme.primary.withValues(alpha: 0.1),
                          child: Icon(Icons.medication,
                              color: theme.colorScheme.primary, size: 20),
                        ),
                        title: Text(p['name'] as String,
                            style: const TextStyle(fontSize: 14)),
                        subtitle: Text('匹配度 ${p['match']}% · ${p['spec']}',
                            style: const TextStyle(fontSize: 12)),
                        trailing: Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.green.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text('${p['match']}%',
                              style: const TextStyle(
                                  fontSize: 12, color: Colors.green)),
                        ),
                      )),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _statItem(String label, String value) {
    return Column(
      children: [
        Text(value,
            style: const TextStyle(
                fontSize: 24, fontWeight: FontWeight.bold)),
        Text(label, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
      ],
    );
  }
}
