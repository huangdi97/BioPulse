import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:one_cloud_app/models/quotation.dart';
import 'package:one_cloud_app/services/database_service.dart';

class QuotationScreen extends StatefulWidget {
  const QuotationScreen({super.key});
  @override
  State<QuotationScreen> createState() => _QuotationScreenState();
}

class _QuotationScreenState extends State<QuotationScreen> {
  List<Quotation> _quotations = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadQuotations();
  }

  Future<void> _loadQuotations() async {
    setState(() => _loading = true);
    final db = context.read<DatabaseService>();
    final list = await db.getQuotations();
    if (mounted) {
      setState(() {
        _quotations = list;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _quotations.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.request_quote,
                          size: 64, color: Colors.grey[400]),
                      const SizedBox(height: 16),
                      Text('暂无报价单',
                          style: TextStyle(color: Colors.grey[600])),
                      const SizedBox(height: 8),
                      Text('从产品匹配中添加产品创建报价单',
                          style: TextStyle(
                              fontSize: 12, color: Colors.grey[500])),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadQuotations,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _quotations.length,
                    itemBuilder: (_, i) {
                      final q = _quotations[i];
                      final products =
                          jsonDecode(q.products) as List? ?? [];
                      final total =
                          products.fold<double>(0, (sum, p) {
                        final price = (p as Map)['price'] as num? ?? 0;
                        return sum + price;
                      });
                      return Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        child: ExpansionTile(
                          leading: CircleAvatar(
                            child: Text('${q.id ?? ''}'),
                          ),
                          title: Text('报价单 #${q.id ?? ''}'),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('PI: ${q.piName}',
                                  style: const TextStyle(fontSize: 12)),
                              Text('¥${total.toStringAsFixed(2)}',
                                  style: TextStyle(
                                      fontSize: 14,
                                      color:
                                          Theme.of(context).colorScheme.primary,
                                      fontWeight: FontWeight.bold)),
                            ],
                          ),
                          children: [
                            ...products.map((p) {
                              final product = p as Map;
                              return ListTile(
                                title: Text(product['name'] as String? ?? ''),
                                subtitle: Text(
                                    '${product['spec']}  |  ¥${product['price']}'),
                                trailing: Chip(
                                  label: Text('${product['match']}%',
                                      style:
                                          const TextStyle(fontSize: 11)),
                                  visualDensity: VisualDensity.compact,
                                ),
                              );
                            }),
                            Padding(
                              padding: const EdgeInsets.all(16),
                              child: Row(
                                children: [
                                  Expanded(
                                    child: OutlinedButton.icon(
                                      onPressed: () =>
                                          _previewQuotation(context, q),
                                      icon: const Icon(Icons.preview, size: 18),
                                      label: const Text('预览'),
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: ElevatedButton.icon(
                                      onPressed: () =>
                                          _sendQuotation(context, q),
                                      icon: const Icon(Icons.send, size: 18),
                                      label: const Text('发送'),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
    );
  }

  void _previewQuotation(BuildContext context, Quotation q) {
    final products = jsonDecode(q.products) as List? ?? [];
    final total = products.fold<double>(0, (sum, p) {
      final price = (p as Map)['price'] as num? ?? 0;
      return sum + price;
    });
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('报价单 #${q.id ?? ''}'),
        content: SizedBox(
          width: double.maxFinite,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('PI: ${q.piName}',
                  style: const TextStyle(fontWeight: FontWeight.w600)),
              const Divider(),
              ...products.map((p) {
                final product = p as Map;
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(child: Text(product['name'] as String? ?? '')),
                      Text('¥${product['price']}'),
                    ],
                  ),
                );
              }),
              const Divider(),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('总计',
                      style: TextStyle(fontWeight: FontWeight.bold)),
                  Text('¥${total.toStringAsFixed(2)}',
                      style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16)),
                ],
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('关闭'),
          ),
        ],
      ),
    );
  }

  void _sendQuotation(BuildContext context, Quotation q) {
    final db = context.read<DatabaseService>();
    final updated = q.copyWith(status: 'sent');
    db.updateQuotation(updated);
    _loadQuotations();
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('报价单已发送')),
    );
  }
}
