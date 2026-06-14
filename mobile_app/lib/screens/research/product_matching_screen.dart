import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:biopulse_app/models/pi_profile.dart';
import 'package:biopulse_app/models/quotation.dart';
import 'package:biopulse_app/services/database_service.dart';
import 'package:biopulse_app/services/api_client.dart';

class ProductMatchingScreen extends StatefulWidget {
  final PIProfile? profile;
  const ProductMatchingScreen({super.key, this.profile});
  @override
  State<ProductMatchingScreen> createState() => _ProductMatchingScreenState();
}

class _ProductMatchingScreenState extends State<ProductMatchingScreen> {
  final List<Map<String, dynamic>> _selectedProducts = [];
  List<Map<String, dynamic>> _allProducts = [];
  bool _productsLoading = true;

  static const _defaultProducts = [
    {'name': '靶向免疫抑制剂-PD1', 'match': 92, 'spec': '100mg/瓶', 'price': 12800},
    {'name': '肿瘤微环境调节剂-TME1', 'match': 88, 'spec': '50mg/片', 'price': 9500},
    {'name': 'VEGF单克隆抗体', 'match': 85, 'spec': '400mg/支', 'price': 15600},
    {'name': 'EGFR-TKI抑制剂', 'match': 82, 'spec': '250mg/粒', 'price': 8200},
    {'name': 'CTLA-4单抗', 'match': 78, 'spec': '200mg/瓶', 'price': 14200},
    {'name': 'mTOR抑制剂', 'match': 75, 'spec': '5mg/片', 'price': 6800},
    {'name': 'CDK4/6抑制剂', 'match': 72, 'spec': '125mg/粒', 'price': 11000},
    {'name': 'PARP抑制剂', 'match': 68, 'spec': '100mg/粒', 'price': 9800},
  ];

  @override
  void initState() {
    super.initState();
    _loadMatchStats();
  }

  Future<void> _loadMatchStats() async {
    try {
      final api = context.read<MultiBackendApiClient>();
      final response = await api
          .getClient('cloud')
          .get<Map<String, dynamic>>('/api/demo/product-match-stats');
      if (response.isSuccess && response.data != null) {
        final categories =
            response.data!['categories'] as List<dynamic>? ?? [];
        setState(() {
          _allProducts = categories.map((c) => {
                'name': c['category'] as String? ?? '',
                'match': ((c['rate'] as num?)?.toDouble() ?? 0 * 100).round(),
                'spec': '共${c['total'] ?? 0}项',
                'price': ((c['matched'] as num?)?.toDouble() ?? 0) * 1000,
              }).toList();
          _productsLoading = false;
        });
        return;
      }
    } catch (_) {}
    setState(() {
      _allProducts = List<Map<String, dynamic>>.from(_defaultProducts);
      _productsLoading = false;
    });
  }

  bool _isSelected(Map<String, dynamic> product) {
    return _selectedProducts.any((p) => p['name'] == product['name']);
  }

  void _toggleProduct(Map<String, dynamic> product) {
    setState(() {
      if (_isSelected(product)) {
        _selectedProducts.removeWhere((p) => p['name'] == product['name']);
      } else {
        _selectedProducts.add(Map.from(product));
      }
    });
  }

  Future<void> _goToQuotation() async {
    if (_selectedProducts.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请至少选择一个产品')),
      );
      return;
    }
    final db = context.read<DatabaseService>();
    await db.insertQuotation(Quotation(
      piName: widget.profile?.name ?? '通用报价',
      products: jsonEncode(_selectedProducts),
      totalAmount: _selectedProducts.fold<double>(
          0, (sum, p) => sum + ((p['price'] as num?)?.toDouble() ?? 0)),
    ));
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('报价单已创建')),
      );
      Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final sorted = List<Map<String, dynamic>>.from(_allProducts)
      ..sort((a, b) => (b['match'] as int).compareTo(a['match'] as int));
    final top3 = sorted.take(3).toList();
    final rest = sorted.skip(3).toList();

    if (widget.profile == null) {
      return Scaffold(
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const SizedBox(height: 8),
            Text('科研产品目录',
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            Text('从PI详情页可查看基于研究领域的匹配推荐',
                style: TextStyle(color: Colors.grey[600])),
            const SizedBox(height: 16),
            ..._allProducts.map((p) => _productCard(p, false, theme)),
          ],
        ),
        bottomNavigationBar: _selectedProducts.isNotEmpty
            ? SafeArea(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: ElevatedButton(
                    onPressed: _goToQuotation,
                    child: Text('添加 ${_selectedProducts.length} 项到报价单'),
                  ),
                ),
              )
            : null,
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('产品匹配')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('基于 ${widget.profile!.name} 的研究领域推荐',
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Text('研究方向: ${widget.profile!.researchAreas}',
              style: TextStyle(color: Colors.grey[600])),
          const SizedBox(height: 16),
          const Text('最佳匹配 Top 3',
              style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          ...top3.map((p) => _productCard(p, true, theme)),
          const SizedBox(height: 16),
          const Text('更多推荐',
              style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          ...rest.map((p) => _productCard(p, false, theme)),
        ],
      ),
      bottomNavigationBar: _selectedProducts.isNotEmpty
          ? SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: ElevatedButton(
                  onPressed: _goToQuotation,
                  child: Text('添加 ${_selectedProducts.length} 项到报价单'),
                ),
              ),
            )
          : null,
    );
  }

  Widget _productCard(
      Map<String, dynamic> product, bool highlight, ThemeData theme) {
    final selected = _isSelected(product);
    return Card(
      color: selected ? theme.colorScheme.primary.withValues(alpha: 0.05) : null,
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: highlight
              ? Colors.amber.withValues(alpha: 0.2)
              : Colors.grey.withValues(alpha: 0.1),
          child: Icon(
            selected ? Icons.check_circle : Icons.medication,
            color: highlight ? Colors.amber : theme.colorScheme.primary,
          ),
        ),
        title: Text(product['name'] as String,
            style: const TextStyle(fontWeight: FontWeight.w500)),
        subtitle:
            Text('规格: ${product['spec']}  |  ¥${product['price']}',
                style: const TextStyle(fontSize: 12)),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.green.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text('${product['match']}%',
                  style: const TextStyle(fontSize: 12, color: Colors.green)),
            ),
            const SizedBox(width: 8),
            IconButton(
              icon: Icon(
                selected
                    ? Icons.remove_circle_outline
                    : Icons.add_circle_outline,
                color: selected ? Colors.red : theme.colorScheme.primary,
              ),
              onPressed: () => _toggleProduct(product),
            ),
          ],
        ),
      ),
    );
  }
}
