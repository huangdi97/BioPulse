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
          .get<List>('/api/pi/search?q=$query');
      if (response.isSuccess && response.data != null) {
        final sources = response.data as List<dynamic>? ?? [];
        final matched = sources.where((s) {
          final name = s['name'] as String? ?? '';
          final inst = s['institution'] as String? ?? '';
          return name.contains(query) || inst.contains(query);
        }).map((s) => PIProfile(
              name: s['name'] as String? ?? '',
              institution: s['institution'] as String? ?? '',
              papersCount: s['total_papers'] as int? ?? 0,
              hIndex: s['h_index'] as int? ?? 0,
              researchAreas: (s['research_areas'] as List?)?.join(', ') ?? '',
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
      setState(() {
        _results = [];
        _loading = false;
        _searched = true;
      });
    } else {
      setState(() {
        _results = results;
        _loading = false;
        _searched = true;
      });
    }
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
