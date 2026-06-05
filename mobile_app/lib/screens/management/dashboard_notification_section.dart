import 'package:flutter/material.dart';
import 'package:one_cloud_app/theme/design_tokens.dart';

class _NotificationItem {
  final String time;
  final String title;
  final String summary;
  final bool isRead;
  const _NotificationItem(this.time, this.title, this.summary, this.isRead);
}

class DashboardNotificationList extends StatelessWidget {
  const DashboardNotificationList({super.key});

  static final _items = [
    _NotificationItem('06-05 14:30', '合规提醒', '请及时提交本月合规报告', false),
    _NotificationItem('06-04 10:00', '培训通知', '新合规政策线上培训开始', true),
    _NotificationItem('06-03 16:45', '系统通知', '您的合规评分已更新', false),
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      children: _items.map((item) => _NotificationTile(item: item)).toList(),
    );
  }
}

class _NotificationTile extends StatelessWidget {
  final _NotificationItem item;
  const _NotificationTile({required this.item});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: DesignTokens.spaceSm),
      padding: const EdgeInsets.all(DesignTokens.spaceSm),
      decoration: BoxDecoration(
        color: item.isRead ? DesignTokens.surfaceCard : DesignTokens.brandLight,
        borderRadius: BorderRadius.circular(DesignTokens.radiusLg),
        border: Border.all(color: DesignTokens.borderDefault),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 8, height: 8,
            margin: const EdgeInsets.only(top: DesignTokens.spaceXs),
            decoration: BoxDecoration(
              color: item.isRead ? DesignTokens.gray30 : DesignTokens.brand,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: DesignTokens.spaceSm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.time, style: const TextStyle(
                  fontSize: 11, color: DesignTokens.textSecondary,
                )),
                const SizedBox(height: DesignTokens.spaceXs),
                Text(item.title, style: DesignTokens.bodySm),
                Text(item.summary, style: const TextStyle(
                  fontSize: 12, color: DesignTokens.textSecondary,
                )),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
