import 'package:flutter/material.dart';
import 'package:biopulse_app/theme/design_tokens.dart';

enum _ComplianceStatus { pass, warn, violation }

class _ComplianceItem {
  final String date;
  final String target;
  final String checkItem;
  final _ComplianceStatus status;
  const _ComplianceItem(this.date, this.target, this.checkItem, this.status);
}

Color complianceStatusColor(_ComplianceStatus status) {
  switch (status) {
    case _ComplianceStatus.pass:
      return DesignTokens.modePass;
    case _ComplianceStatus.warn:
      return DesignTokens.modeWarn;
    case _ComplianceStatus.violation:
      return DesignTokens.error;
  }
}

String complianceStatusLabel(_ComplianceStatus status) {
  switch (status) {
    case _ComplianceStatus.pass:
      return '通过';
    case _ComplianceStatus.warn:
      return '警告';
    case _ComplianceStatus.violation:
      return '违规';
  }
}

class DashboardComplianceList extends StatelessWidget {
  const DashboardComplianceList({super.key});

  static final _items = [
    _ComplianceItem('2026-06-05', '李医生', '学术推广材料', _ComplianceStatus.pass),
    _ComplianceItem('2026-06-04', '王主任', '费用报销', _ComplianceStatus.pass),
    _ComplianceItem('2026-06-03', '张教授', '会议申请', _ComplianceStatus.warn),
    _ComplianceItem('2026-06-02', '赵医生', '样品发放', _ComplianceStatus.violation),
    _ComplianceItem('2026-06-01', '刘主任', '拜访记录', _ComplianceStatus.pass),
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      children: _items.map((item) => _ComplianceTile(item: item)).toList(),
    );
  }
}

class _ComplianceTile extends StatelessWidget {
  final _ComplianceItem item;
  const _ComplianceTile({required this.item});

  @override
  Widget build(BuildContext context) {
    final color = complianceStatusColor(item.status);
    final label = complianceStatusLabel(item.status);
    return Container(
      margin: const EdgeInsets.only(bottom: DesignTokens.spaceSm),
      padding: const EdgeInsets.all(DesignTokens.spaceSm),
      decoration: BoxDecoration(
        color: DesignTokens.surfaceCard,
        borderRadius: BorderRadius.circular(DesignTokens.radiusLg),
        border: Border.all(color: DesignTokens.borderDefault),
      ),
      child: Row(
        children: [
          Container(width: 8, height: 8,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: DesignTokens.spaceSm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('${item.date}  ${item.target}', style: DesignTokens.bodySm),
                Text(item.checkItem, style: const TextStyle(
                  fontSize: 12, color: DesignTokens.textSecondary,
                )),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(
              horizontal: DesignTokens.spaceSm, vertical: DesignTokens.spaceXs,
            ),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(DesignTokens.radiusSm),
            ),
            child: Text(label, style: TextStyle(
              fontSize: 11, fontWeight: FontWeight.w600, color: color,
            )),
          ),
        ],
      ),
    );
  }
}
