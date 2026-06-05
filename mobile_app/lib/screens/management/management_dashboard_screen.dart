import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:one_cloud_app/providers/mode_provider.dart';
import 'package:one_cloud_app/theme/design_tokens.dart';
import 'package:one_cloud_app/services/api_client.dart';
import 'package:one_cloud_app/screens/management/dashboard_compliance_section.dart';
import 'package:one_cloud_app/screens/management/dashboard_notification_section.dart';

class ManagementDashboardScreen extends StatefulWidget {
  const ManagementDashboardScreen({super.key});

  @override
  State<ManagementDashboardScreen> createState() => _ManagementDashboardScreenState();
}

class _ManagementDashboardScreenState extends State<ManagementDashboardScreen> {
  @override
  void initState() {
    super.initState();
    _loadDashboard();
  }

  Future<void> _loadDashboard() async {
    try {
      final api = context.read<MultiBackendApiClient>();
      await api.getClient('cloud').get('/api/demo/dashboard');
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    final mode = context.watch<ModeProvider>();
    final role = mode.currentMode == AppMode.research ? '科研销售' : '药代';

    return Scaffold(
      appBar: AppBar(
        title: const Text('管理'),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_outlined),
            onPressed: () => Navigator.pushNamed(context, '/management/notifications'),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(DesignTokens.spaceMd),
        children: [
          _WelcomeHeader(role: role),
          const SizedBox(height: DesignTokens.spaceMd),
          const _StatsRow(),
          const SizedBox(height: DesignTokens.spaceLg),
          _SectionHeader(
            title: '最近合规记录',
            onViewAll: () => Navigator.pushNamed(context, '/management/compliance'),
          ),
          const SizedBox(height: DesignTokens.spaceSm),
          const DashboardComplianceList(),
          const SizedBox(height: DesignTokens.spaceLg),
          const _SectionHeader(title: '通知'),
          const SizedBox(height: DesignTokens.spaceSm),
          const DashboardNotificationList(),
        ],
      ),
    );
  }
}

class _WelcomeHeader extends StatelessWidget {
  final String role;
  const _WelcomeHeader({required this.role});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(DesignTokens.spaceMd),
      decoration: BoxDecoration(
        color: DesignTokens.brandLight,
        borderRadius: BorderRadius.circular(DesignTokens.radiusLg),
      ),
      child: Row(
        children: [
          const CircleAvatar(
            radius: 24,
            backgroundColor: DesignTokens.brand,
            child: Icon(Icons.person, color: DesignTokens.white, size: 28),
          ),
          const SizedBox(width: DesignTokens.spaceMd),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('欢迎回来', style: DesignTokens.bodySm),
              const SizedBox(height: DesignTokens.spaceXs),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: DesignTokens.spaceSm,
                  vertical: DesignTokens.spaceXs,
                ),
                decoration: BoxDecoration(
                  color: DesignTokens.modePharma.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(DesignTokens.radiusSm),
                ),
                child: Text(role,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: DesignTokens.modePharma,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _StatsRow extends StatelessWidget {
  const _StatsRow();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 100,
      child: ListView(
        scrollDirection: Axis.horizontal,
        children: const [
          _StatCard(label: '本月拜访数', value: '24', icon: Icons.calendar_today),
          SizedBox(width: DesignTokens.spaceSm),
          _StatCard(label: '合规率', value: '92%', icon: Icons.verified),
          SizedBox(width: DesignTokens.spaceSm),
          _StatCard(label: '任务完成', value: '18', icon: Icons.task_alt),
        ],
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  const _StatCard({required this.label, required this.value, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 140,
      padding: const EdgeInsets.all(DesignTokens.spaceMd),
      decoration: BoxDecoration(
        color: DesignTokens.surfaceCard,
        borderRadius: BorderRadius.circular(DesignTokens.radiusLg),
        border: Border.all(color: DesignTokens.borderDefault),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 20, color: DesignTokens.brand),
          const SizedBox(height: DesignTokens.spaceSm),
          Text(value, style: DesignTokens.h3),
          Text(label, style: const TextStyle(
            fontSize: 12, color: DesignTokens.textSecondary,
          )),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  final VoidCallback? onViewAll;
  const _SectionHeader({required this.title, this.onViewAll});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(title, style: DesignTokens.h3),
        if (onViewAll != null)
          TextButton(
            onPressed: onViewAll,
            child: const Text('查看全部', style: TextStyle(fontSize: 13, color: DesignTokens.brand)),
          ),
      ],
    );
  }
}
