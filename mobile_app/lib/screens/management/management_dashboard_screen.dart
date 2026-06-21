import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:provider/provider.dart';
import 'package:biopulse_app/constants/app_constants.dart';
import 'package:biopulse_app/providers/mode_provider.dart';
import 'package:biopulse_app/theme/design_tokens.dart';
import 'package:biopulse_app/services/api_client.dart';
import 'package:biopulse_app/services/push_service.dart';
import 'package:biopulse_app/services/cache_service.dart';
import 'package:biopulse_app/services/database_service.dart';
import 'package:biopulse_app/screens/management/dashboard_compliance_section.dart';
import 'package:biopulse_app/screens/management/dashboard_notification_section.dart';
import 'package:biopulse_app/widgets/agent_insight_bar.dart';

class ManagementDashboardScreen extends StatefulWidget {
  const ManagementDashboardScreen({super.key});

  @override
  State<ManagementDashboardScreen> createState() => _ManagementDashboardScreenState();
}

class _ManagementDashboardScreenState extends State<ManagementDashboardScreen> with WidgetsBindingObserver {
  final DatabaseService _db = DatabaseService();
  late final CacheService _cacheService;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _cacheService = CacheService(_db);
    _initDb();
    _loadDashboard();
    _initPushService();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _loadDashboard();
    }
  }

  Future<void> _initDb() async {
    await _db.initDatabase();
  }

  Future<void> _initPushService() async {
    final push = PushService();
    await push.initialize();
    await push.registerForPush();
  }

  Future<void> _loadDashboard() async {
    try {
      final api = context.read<MultiBackendApiClient>();
      await api.getClient('cloud').get('/api/demo/dashboard');
      _cacheInsights();
    } catch (_) {
      _loadCachedInsights();
    }
  }

  Future<void> _cacheInsights() async {
    try {
      final api = context.read<MultiBackendApiClient>();
      final response = await api.getClient('cloud').get<List>('/api/v1/agent/insights');
      if (response.data != null) {
        await _cacheService.cacheInsights('current_user', jsonEncode(response.data));
        await _cacheService.clearExpiredCache();
      }
    } catch (_) {}
  }

  Future<void> _loadCachedInsights() async {
    final cached = await _cacheService.getCachedInsights('current_user');
    if (cached != null && mounted) {
      debugPrint('Loaded cached insights: $cached');
    }
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
          const SizedBox(height: DesignTokens.spaceMd),
          const AgentInsightBar(pageId: 'mobile_mgmt_dash'),
          const SizedBox(height: DesignTokens.spaceMd),
          _AiCapabilitySection(),
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

class _AiCapabilitySection extends StatelessWidget {
  const _AiCapabilitySection();

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('AI 能力', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
        const SizedBox(height: DesignTokens.spaceSm),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              _AiCapabilityCard(
                icon: Icons.mic,
                label: 'ASR转录',
                description: '语音实时转文字',
              ),
              const SizedBox(width: DesignTokens.spaceSm),
              _AiCapabilityCard(
                icon: Icons.notifications_active,
                label: '智能提醒',
                description: '自动生成提醒事项',
              ),
              const SizedBox(width: DesignTokens.spaceSm),
              _AiCapabilityCard(
                icon: Icons.tips_and_updates,
                label: '拜访建议',
                description: '个性化沟通策略',
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _AiCapabilityCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String description;

  const _AiCapabilityCard({
    required this.icon,
    required this.label,
    required this.description,
  });

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
          Row(
            children: [
              Icon(icon, size: 20, color: DesignTokens.brand),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.yellow.shade50,
                  borderRadius: BorderRadius.circular(DesignTokens.radiusPill),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.circle, size: 6, color: Colors.yellow),
                    SizedBox(width: 3),
                    Text('模拟', style: TextStyle(fontSize: 10, color: Colors.brown)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: DesignTokens.spaceSm),
          Text(label, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
          const SizedBox(height: 2),
          Text(description, style: TextStyle(fontSize: 11, color: Colors.grey[600])),
        ],
      ),
    );
  }
}
