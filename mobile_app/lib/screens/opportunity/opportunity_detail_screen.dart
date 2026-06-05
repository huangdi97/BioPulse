import 'package:flutter/material.dart';

const _mockDetailData = {
  '1': {'name': '关节镜设备采购', 'customer': '市第一人民医院', 'amount': '¥12.0万', 'stage': '跟进中', 'date': '2026-06-01', 'notes': '已提交初步方案'},
  '2': {'name': '骨科植入物供应', 'customer': '市中心医院', 'amount': '¥8.5万', 'stage': '跟进中', 'date': '2026-05-28', 'notes': '第二次拜访完成'},
  '3': {'name': '手术导航系统', 'customer': '省立医院', 'amount': '¥30.0万', 'stage': '已转化', 'date': '2026-05-20', 'notes': '合同已签署'},
  '4': {'name': '康复设备租赁', 'customer': '康复医院', 'amount': '¥4.5万', 'stage': '已关闭', 'date': '2026-05-15', 'notes': '客户预算不足'},
  '5': {'name': 'CT影像系统升级', 'customer': '人民医院', 'amount': '¥20.0万', 'stage': '跟进中', 'date': '2026-06-03', 'notes': '技术交流已完成'},
};

class OpportunityDetailScreen extends StatelessWidget {
  const OpportunityDetailScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final id = ModalRoute.of(context)!.settings.arguments as String;
    final data = _mockDetailData[id]!;
    final theme = Theme.of(context);

    void snack(String msg) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));

    return Scaffold(
      appBar: AppBar(title: Text(data['name']!)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(data['name']!, style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  _row('客户', data['customer']!),
                  _row('金额', data['amount']!),
                  _row('阶段', data['stage']!),
                  _row('日期', data['date']!),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('备注', style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  Text(data['notes']!, style: TextStyle(color: Colors.grey[700])),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              Expanded(child: ElevatedButton.icon(onPressed: () => snack('已记录跟进'), icon: const Icon(Icons.follow_the_signs), label: const Text('跟进'))),
              const SizedBox(width: 8),
              Expanded(child: ElevatedButton.icon(onPressed: () => snack('已标记为转化'), icon: const Icon(Icons.check_circle), label: const Text('转化'))),
              const SizedBox(width: 8),
              Expanded(child: ElevatedButton.icon(onPressed: () => snack('已关闭'), icon: const Icon(Icons.cancel), label: const Text('关闭'))),
            ],
          ),
        ],
      ),
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          SizedBox(width: 60, child: Text(label, style: TextStyle(color: Colors.grey[600]))),
          Expanded(child: Text(value, style: const TextStyle(fontWeight: FontWeight.w500))),
        ],
      ),
    );
  }
}
