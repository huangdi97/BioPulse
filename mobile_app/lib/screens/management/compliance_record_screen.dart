import 'package:flutter/material.dart';
import 'package:one_cloud_app/theme/design_tokens.dart';

enum _ComplianceFilter { all, pass, warn, violation }

class ComplianceRecordScreen extends StatefulWidget {
  const ComplianceRecordScreen({super.key});

  @override
  State<ComplianceRecordScreen> createState() => _ComplianceRecordScreenState();
}

class _ComplianceRecordScreenState extends State<ComplianceRecordScreen> {
  _ComplianceFilter _filter = _ComplianceFilter.all;

  static final _items = [
    _Record('2026-06-05', '李医生', '学术推广材料', _Status.pass, '内容符合规范，无违规表述'),
    _Record('2026-06-04', '王主任', '费用报销', _Status.pass, '报销流程完整，凭证齐全'),
    _Record('2026-06-03', '张教授', '会议申请', _Status.warn, '预算超支20%，需补充说明'),
    _Record('2026-06-02', '赵医生', '样品发放', _Status.violation, '未按规定登记样品批号'),
    _Record('2026-06-01', '刘主任', '拜访记录', _Status.pass, '拜访记录完整'),
    _Record('2026-05-30', '陈教授', '学术赞助', _Status.warn, '赞助金额超出审批额度'),
    _Record('2026-05-28', '孙医生', '科室会', _Status.pass, '会议资料齐全'),
    _Record('2026-05-25', '周主任', '礼品赠送', _Status.violation, '礼品价值超过规定上限'),
  ];

  List<_Record> get _filteredItems {
    switch (_filter) {
      case _ComplianceFilter.all:
        return _items;
      case _ComplianceFilter.pass:
        return _items.where((i) => i.status == _Status.pass).toList();
      case _ComplianceFilter.warn:
        return _items.where((i) => i.status == _Status.warn).toList();
      case _ComplianceFilter.violation:
        return _items.where((i) => i.status == _Status.violation).toList();
    }
  }

  @override
  Widget build(BuildContext context) {
    final items = _filteredItems;
    return Scaffold(
      appBar: AppBar(title: const Text('合规记录')),
      body: Column(
        children: [
          _FilterBar(
            selected: _filter,
            onChanged: (f) => setState(() => _filter = f),
          ),
          Expanded(
            child: items.isEmpty
                ? const Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.inbox_outlined, size: 48, color: DesignTokens.gray30),
                        SizedBox(height: DesignTokens.spaceSm),
                        Text('暂无合规记录', style: TextStyle(
                          fontSize: 14,
                          color: DesignTokens.textSecondary,
                        )),
                      ],
                    ),
                  )
                : ListView.separated(
                    padding: const EdgeInsets.all(DesignTokens.spaceMd),
                    itemCount: items.length,
                    separatorBuilder: (_, __) => const SizedBox(height: DesignTokens.spaceSm),
                    itemBuilder: (context, index) {
                      final item = items[index];
                      return _RecordTile(
                        item: item,
                        onTap: () => _showDetail(context, item),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  void _showDetail(BuildContext context, _Record item) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(DesignTokens.radiusXl)),
      ),
      builder: (_) => Padding(
        padding: const EdgeInsets.all(DesignTokens.spaceMd),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 32, height: 4,
                decoration: BoxDecoration(
                  color: DesignTokens.gray30,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: DesignTokens.spaceMd),
            Text('合规详情', style: DesignTokens.h3),
            const SizedBox(height: DesignTokens.spaceMd),
            _detailRow('日期', item.date),
            _detailRow('拜访对象', item.target),
            _detailRow('检查项', item.checkItem),
            _detailRow('状态', item.statusLabel),
            const SizedBox(height: DesignTokens.spaceSm),
            const Text('备注', style: DesignTokens.label),
            const SizedBox(height: DesignTokens.spaceXs),
            Text(item.detail, style: DesignTokens.bodySm),
            const SizedBox(height: DesignTokens.spaceMd),
          ],
        ),
      ),
    );
  }

  Widget _detailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: DesignTokens.spaceSm),
      child: Row(
        children: [
          SizedBox(
            width: 72,
            child: Text(label, style: const TextStyle(
              fontSize: 13,
              color: DesignTokens.textSecondary,
            )),
          ),
          Expanded(child: Text(value, style: DesignTokens.bodySm)),
        ],
      ),
    );
  }
}

enum _Status { pass, warn, violation }

class _Record {
  final String date;
  final String target;
  final String checkItem;
  final _Status status;
  final String detail;
  const _Record(this.date, this.target, this.checkItem, this.status, this.detail);

  String get statusLabel {
    switch (status) {
      case _Status.pass:
        return '通过';
      case _Status.warn:
        return '警告';
      case _Status.violation:
        return '违规';
    }
  }

  Color get statusColor {
    switch (status) {
      case _Status.pass:
        return DesignTokens.modePass;
      case _Status.warn:
        return DesignTokens.modeWarn;
      case _Status.violation:
        return DesignTokens.error;
    }
  }
}

class _FilterBar extends StatelessWidget {
  final _ComplianceFilter selected;
  final ValueChanged<_ComplianceFilter> onChanged;
  const _FilterBar({required this.selected, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final filters = [
      (_ComplianceFilter.all, '全部'),
      (_ComplianceFilter.pass, '通过'),
      (_ComplianceFilter.warn, '警告'),
      (_ComplianceFilter.violation, '违规'),
    ];
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: DesignTokens.spaceMd,
        vertical: DesignTokens.spaceSm,
      ),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: DesignTokens.borderDefault)),
      ),
      child: Row(
        children: filters.map((f) {
          final (filter, label) = f;
          final isSelected = filter == selected;
          return Padding(
            padding: const EdgeInsets.only(right: DesignTokens.spaceSm),
            child: ChoiceChip(
              label: Text(label),
              selected: isSelected,
              onSelected: (_) => onChanged(filter),
              selectedColor: DesignTokens.brandLight,
              labelStyle: TextStyle(
                fontSize: 13,
                color: isSelected ? DesignTokens.brand : DesignTokens.textSecondary,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
              ),
              side: BorderSide(
                color: isSelected ? DesignTokens.brand : DesignTokens.borderDefault,
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}

class _RecordTile extends StatelessWidget {
  final _Record item;
  final VoidCallback onTap;
  const _RecordTile({required this.item, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: DesignTokens.surfaceCard,
      borderRadius: BorderRadius.circular(DesignTokens.radiusLg),
      child: InkWell(
        borderRadius: BorderRadius.circular(DesignTokens.radiusLg),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(DesignTokens.spaceSm),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(DesignTokens.radiusLg),
            border: Border.all(color: DesignTokens.borderDefault),
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(item.date, style: const TextStyle(
                          fontSize: 12,
                          color: DesignTokens.textSecondary,
                        )),
                        const SizedBox(width: DesignTokens.spaceSm),
                        Text(item.target, style: DesignTokens.bodySm),
                      ],
                    ),
                    const SizedBox(height: DesignTokens.spaceXs),
                    Text(item.checkItem, style: const TextStyle(
                      fontSize: 12,
                      color: DesignTokens.textSecondary,
                    )),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: DesignTokens.spaceSm,
                  vertical: DesignTokens.spaceXs,
                ),
                decoration: BoxDecoration(
                  color: item.statusColor.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(DesignTokens.radiusSm),
                ),
                child: Text(item.statusLabel, style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: item.statusColor,
                )),
              ),
              const SizedBox(width: DesignTokens.spaceXs),
              const Icon(Icons.chevron_right, size: 18, color: DesignTokens.gray50),
            ],
          ),
        ),
      ),
    );
  }
}
