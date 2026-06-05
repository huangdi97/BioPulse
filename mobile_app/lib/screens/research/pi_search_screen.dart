import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:one_cloud_app/models/pi_profile.dart';
import 'package:one_cloud_app/services/database_service.dart';
import 'package:one_cloud_app/services/api_client.dart';
import 'package:one_cloud_app/screens/research/pi_detail_screen.dart';

class PISearchScreen extends StatefulWidget {
  const PISearchScreen({super.key});
  @override
  State<PISearchScreen> createState() => _PISearchScreenState();
}

class _PISearchScreenState extends State<PISearchScreen> {
  final _searchController = TextEditingController();
  List<PIProfile> _results = [];
  bool _loading = false;
  bool _searched = false;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _search() async {
    final query = _searchController.text.trim();
    if (query.isEmpty) return;
    setState(() => _loading = true);
    try {
      final api = context.read<MultiBackendApiClient>();
      final response = await api
          .getClient('cloud')
          .get<Map<String, dynamic>>('/api/demo/pi-sources');
      if (response.isSuccess && response.data != null) {
        final sources = response.data!['pi_sources'] as List<dynamic>? ?? [];
        final matched = sources.where((s) {
          final name = s['name'] as String? ?? '';
          final inst = s['institution'] as String? ?? '';
          return name.contains(query) || inst.contains(query);
        }).map((s) => PIProfile(
              name: s['name'] as String? ?? '',
              institution: s['institution'] as String? ?? '',
              papersCount: s['matches'] as int? ?? 0,
              hIndex: 0,
              researchAreas: '',
            )).toList();
        if (mounted) {
          setState(() {
            _results = matched;
            _loading = false;
            _searched = true;
          });
        }
        return;
      }
    } catch (_) {}
    final db = context.read<DatabaseService>();
    final results = await db.searchPIProfiles(query);
    if (results.isEmpty) {
      await _loadMockData(query);
    } else {
      setState(() {
        _results = results;
        _loading = false;
        _searched = true;
      });
    }
  }

  Future<void> _loadMockData(String query) async {
    final db = context.read<DatabaseService>();
    final mockData = [
      PIProfile(
        name: '张伟',
        institution: '北京大学第一医院',
        papersCount: 86,
        hIndex: 32,
        researchAreas: '肿瘤免疫,靶向治疗,肿瘤微环境',
        activeYears: '2008-2026',
        bio: '肿瘤学领域专家，主持多项国家级课题',
      ),
      PIProfile(
        name: '李强',
        institution: '上海交通大学医学院附属瑞金医院',
        papersCount: 124,
        hIndex: 45,
        researchAreas: '心血管疾病,高血压,动脉粥样硬化',
        activeYears: '2005-2026',
        bio: '心血管领域权威专家，发表多篇顶级期刊论文',
      ),
      PIProfile(
        name: '王芳',
        institution: '复旦大学附属中山医院',
        papersCount: 67,
        hIndex: 28,
        researchAreas: '糖尿病,代谢综合征,内分泌',
        activeYears: '2010-2026',
        bio: '内分泌与代谢病专家',
      ),
      PIProfile(
        name: '刘洋',
        institution: '华中科技大学同济医学院',
        papersCount: 93,
        hIndex: 38,
        researchAreas: '神经退行性疾病,阿尔茨海默病,神经保护',
        activeYears: '2009-2026',
        bio: '神经科学领域知名研究者',
      ),
    ];
    final matched = mockData
        .where((p) =>
            p.name.contains(query) || p.institution.contains(query))
        .toList();
    for (final p in matched) {
      await db.insertPIProfile(p);
    }
    if (matched.isEmpty) {
      final fallback = PIProfile(
        name: query,
        institution: '未知机构',
        papersCount: 0,
        hIndex: 0,
        researchAreas: '',
        activeYears: '',
      );
      await db.insertPIProfile(fallback);
      matched.add(fallback);
    }
    setState(() {
      _results = matched;
      _loading = false;
      _searched = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: '搜索PI姓名或机构...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchController.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _searchController.clear();
                          setState(() {
                            _results = [];
                            _searched = false;
                          });
                        },
                      )
                    : null,
                border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12)),
              ),
              onSubmitted: (_) => _search(),
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : !_searched
                    ? Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.science,
                                size: 64, color: Colors.grey[400]),
                            const SizedBox(height: 16),
                            Text('搜索PI研究者',
                                style: TextStyle(color: Colors.grey[600])),
                          ],
                        ),
                      )
                    : _results.isEmpty
                        ? Center(
                            child: Text('未找到匹配的研究者',
                                style: TextStyle(color: Colors.grey[500])))
                        : ListView.builder(
                            padding: const EdgeInsets.symmetric(horizontal: 16),
                            itemCount: _results.length,
                            itemBuilder: (_, i) {
                              final p = _results[i];
                              return Card(
                                margin: const EdgeInsets.only(bottom: 8),
                                child: ListTile(
                                  leading: CircleAvatar(
                                    child: Text(p.name.isNotEmpty
                                        ? p.name[0]
                                        : '?'),
                                  ),
                                  title: Text(p.name,
                                      style: const TextStyle(
                                          fontWeight: FontWeight.w600)),
                                  subtitle: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(p.institution,
                                          style: const TextStyle(fontSize: 12)),
                                      const SizedBox(height: 4),
                                      Row(
                                        children: [
                                          _infoChip('论文', p.papersCount),
                                          const SizedBox(width: 8),
                                          _infoChip('H指数', p.hIndex),
                                        ],
                                      ),
                                    ],
                                  ),
                                  isThreeLine: true,
                                  onTap: () {
                                    Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder: (_) =>
                                            PIDetailScreen(profile: p),
                                      ),
                                    );
                                  },
                                ),
                              );
                            },
                          ),
          ),
        ],
      ),
    );
  }

  Widget _infoChip(String label, int value) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text('$label: $value',
          style: const TextStyle(fontSize: 11, color: Colors.grey)),
    );
  }
}
