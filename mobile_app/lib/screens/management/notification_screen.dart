import 'package:flutter/material.dart';
import 'package:one_cloud_app/theme/design_tokens.dart';

class NotificationScreen extends StatefulWidget {
  const NotificationScreen({super.key});

  @override
  State<NotificationScreen> createState() => _NotificationScreenState();
}

class _NotificationScreenState extends State<NotificationScreen> {
  final _items = [
    _NotificationItem('2026-06-05 14:30', '合规提醒', '请及时提交本月合规报告，截止日期为下周五。', false),
    _NotificationItem('2026-06-04 10:00', '培训通知', '新合规政策线上培训将于本周五下午2点开始。', false),
    _NotificationItem('2026-06-03 16:45', '系统通知', '您的合规评分已更新为92分，较上月提升5分。', false),
    _NotificationItem('2026-06-02 09:00', '合规提醒', '上月合规报告已审核通过，请查看详情。', true),
    _NotificationItem('2026-06-01 11:20', '系统通知', '欢迎使用新版管理后台。', true),
  ];

  void _markAllAsRead() {
    setState(() {
      for (final item in _items) {
        item.isRead = true;
      }
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('已全部标记为已读'), duration: Duration(seconds: 2)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final hasUnread = _items.any((i) => !i.isRead);
    return Scaffold(
      appBar: AppBar(
        title: const Text('通知中心'),
        actions: [
          if (hasUnread)
            TextButton(
              onPressed: _markAllAsRead,
              child: const Text('全部已读', style: TextStyle(fontSize: 13, color: DesignTokens.brand)),
            ),
        ],
      ),
      body: _items.isEmpty
          ? const Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.notifications_none_outlined, size: 48, color: DesignTokens.gray30),
                  SizedBox(height: DesignTokens.spaceSm),
                  Text('暂无通知', style: TextStyle(
                    fontSize: 14,
                    color: DesignTokens.textSecondary,
                  )),
                ],
              ),
            )
          : ListView.separated(
              padding: const EdgeInsets.all(DesignTokens.spaceMd),
              itemCount: _items.length,
              separatorBuilder: (_, __) => const SizedBox(height: DesignTokens.spaceSm),
              itemBuilder: (context, index) {
                final item = _items[index];
                return _NotificationTile(
                  item: item,
                  onTap: () {
                    if (!item.isRead) {
                      setState(() => item.isRead = true);
                    }
                  },
                );
              },
            ),
    );
  }
}

class _NotificationItem {
  final String time;
  final String title;
  final String summary;
  bool isRead;
  _NotificationItem(this.time, this.title, this.summary, this.isRead);
}

class _NotificationTile extends StatelessWidget {
  final _NotificationItem item;
  final VoidCallback onTap;
  const _NotificationTile({required this.item, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: item.isRead ? DesignTokens.surfaceCard : DesignTokens.brandLight,
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
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 8,
                height: 8,
                margin: const EdgeInsets.only(top: DesignTokens.spaceXs + 2),
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
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(item.title, style: DesignTokens.bodySm),
                        Text(item.time, style: const TextStyle(
                          fontSize: 11,
                          color: DesignTokens.textSecondary,
                        )),
                      ],
                    ),
                    const SizedBox(height: DesignTokens.spaceXs),
                    Text(item.summary, style: const TextStyle(
                      fontSize: 12,
                      color: DesignTokens.textSecondary,
                    )),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
