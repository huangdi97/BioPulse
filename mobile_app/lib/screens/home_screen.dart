import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:one_cloud_app/providers/auth_provider.dart';
import 'package:one_cloud_app/providers/mode_provider.dart';
import 'package:one_cloud_app/screens/settings_screen.dart';
import 'package:one_cloud_app/screens/pharma/visit_list_screen.dart';
import 'package:one_cloud_app/screens/pharma/hcp_list_screen.dart';
import 'package:one_cloud_app/screens/pharma/compliance_screen.dart';
import 'package:one_cloud_app/screens/surgery/surgery_list_screen.dart';
import 'package:one_cloud_app/screens/surgery/scan_screen.dart';
import 'package:one_cloud_app/screens/research/pi_search_screen.dart';
import 'package:one_cloud_app/screens/research/product_matching_screen.dart';
import 'package:one_cloud_app/screens/research/quotation_screen.dart';
import 'package:one_cloud_app/screens/opportunity/opportunity_list_screen.dart';
import 'package:one_cloud_app/screens/sales_coach/training_list_screen.dart';
import 'package:one_cloud_app/screens/sales_coach/analysis_report_screen.dart';
import 'package:one_cloud_app/screens/sales_coach/recommendation_screen.dart';
import 'package:one_cloud_app/screens/management/management_dashboard_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  static const _modeLabels = {
    AppMode.pharma: '医药模式',
    AppMode.surgery: '手术模式',
    AppMode.opportunity: '商机模式',
    AppMode.salesCoach: '销售教练模式',
    AppMode.research: '研究模式',
  };

  String _scopeFromMode(AppMode mode) {
    switch (mode) {
      case AppMode.pharma:
        return 'pharma';
      case AppMode.surgery:
        return 'surgery';
      case AppMode.opportunity:
        return 'opportunity';
      case AppMode.salesCoach:
        return 'salesCoach';
      case AppMode.research:
        return 'research';
    }
  }

  void _onItemTapped(int index) => setState(() => _currentIndex = index);

  Future<void> _switchMode(AppMode mode) async {
    final auth = context.read<AuthProvider>();
    final success = await auth.switchModeWithScope(_scopeFromMode(mode));
    if (success) {
      await context.read<ModeProvider>().switchMode(mode);
      setState(() => _currentIndex = 0);
    }
  }

  Future<void> _logout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('确认退出'),
        content: const Text('确定要退出登录吗？'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('取消')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('确认')),
        ],
      ),
    );
    if (confirmed == true && mounted) {
      await context.read<AuthProvider>().logout();
      if (mounted) Navigator.pushReplacementNamed(context, '/login');
    }
  }

  List<Widget> _pages(AppMode mode) {
    switch (mode) {
      case AppMode.pharma:
        return const [
          VisitListScreen(),
          HcpListScreen(),
          ComplianceScreen(),
          SurgeryListScreen(),
          ManagementDashboardScreen(),
          SettingsScreen(),
        ];
      case AppMode.surgery:
        return const [
          SurgeryListScreen(),
          ScanScreen(),
          ManagementDashboardScreen(),
          SettingsScreen(),
        ];
      case AppMode.opportunity:
        return const [
          OpportunityListScreen(),
          ManagementDashboardScreen(),
          SettingsScreen(),
        ];
      case AppMode.salesCoach:
        return const [
          TrainingListScreen(),
          AnalysisReportScreen(),
          RecommendationScreen(),
          ManagementDashboardScreen(),
          SettingsScreen(),
        ];
      case AppMode.research:
        return const [
          PISearchScreen(),
          ProductMatchingScreen(),
          QuotationScreen(),
          ManagementDashboardScreen(),
          SettingsScreen(),
        ];
    }
  }

  List<NavigationDestination> _destinations(AppMode mode) {
    switch (mode) {
      case AppMode.pharma:
        return const [
          NavigationDestination(icon: Icon(Icons.calendar_today_outlined), selectedIcon: Icon(Icons.calendar_today), label: '拜访'),
          NavigationDestination(icon: Icon(Icons.people_outline), selectedIcon: Icon(Icons.people), label: 'HCP'),
          NavigationDestination(icon: Icon(Icons.verified_outlined), selectedIcon: Icon(Icons.verified), label: '合规'),
          NavigationDestination(icon: Icon(Icons.local_hospital_outlined), selectedIcon: Icon(Icons.local_hospital), label: '手术'),
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard), label: '管理'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: '设置'),
        ];
      case AppMode.surgery:
        return const [
          NavigationDestination(icon: Icon(Icons.local_hospital_outlined), selectedIcon: Icon(Icons.local_hospital), label: '手术'),
          NavigationDestination(icon: Icon(Icons.qr_code_scanner_outlined), selectedIcon: Icon(Icons.qr_code_scanner), label: '扫描'),
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard), label: '管理'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: '设置'),
        ];
      case AppMode.opportunity:
        return const [
          NavigationDestination(icon: Icon(Icons.trending_up_outlined), selectedIcon: Icon(Icons.trending_up), label: '商机'),
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard), label: '管理'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: '设置'),
        ];
      case AppMode.salesCoach:
        return const [
          NavigationDestination(icon: Icon(Icons.school_outlined), selectedIcon: Icon(Icons.school), label: '培训'),
          NavigationDestination(icon: Icon(Icons.assessment_outlined), selectedIcon: Icon(Icons.assessment), label: '报告'),
          NavigationDestination(icon: Icon(Icons.lightbulb_outline), selectedIcon: Icon(Icons.lightbulb), label: '推荐'),
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard), label: '管理'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: '设置'),
        ];
      case AppMode.research:
        return const [
          NavigationDestination(icon: Icon(Icons.search_outlined), selectedIcon: Icon(Icons.search), label: 'PI搜索'),
          NavigationDestination(icon: Icon(Icons.mediation_outlined), selectedIcon: Icon(Icons.mediation), label: '匹配'),
          NavigationDestination(icon: Icon(Icons.request_quote_outlined), selectedIcon: Icon(Icons.request_quote), label: '报价'),
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard), label: '管理'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: '设置'),
        ];
    }
  }

  @override
  Widget build(BuildContext context) {
    final mode = context.watch<ModeProvider>();
    final auth = context.watch<AuthProvider>();
    final pages = _pages(mode.currentMode);
    final destinations = _destinations(mode.currentMode);

    if (_currentIndex >= pages.length) _currentIndex = 0;

    return Scaffold(
      appBar: AppBar(
        title: Text(_modeLabels[mode.currentMode]!),
        actions: [
          PopupMenuButton<AppMode>(
            icon: const Icon(Icons.swap_horiz),
            tooltip: '切换模式',
            onSelected: _switchMode,
            itemBuilder: (context) => [
              for (final m in AppMode.values)
                if (m != mode.currentMode)
                  PopupMenuItem(value: m, child: Text(_modeLabels[m]!)),
            ],
          ),
        ],
      ),
      drawer: _buildDrawer(context, auth, mode),
      body: pages[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: _onItemTapped,
        destinations: destinations,
      ),
    );
  }

  Widget _buildDrawer(BuildContext context, AuthProvider auth, ModeProvider mode) {
    final theme = Theme.of(context);

    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          DrawerHeader(
            decoration: BoxDecoration(color: theme.colorScheme.primary),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                const CircleAvatar(radius: 28, child: Icon(Icons.person, size: 32)),
                const SizedBox(height: 12),
                Text(auth.user?['username'] as String? ?? '用户',
                    style: const TextStyle(color: Colors.white, fontSize: 18)),
                Text(_modeLabels[mode.currentMode]!,
                    style: TextStyle(color: Colors.white.withValues(alpha: 0.8))),
              ],
            ),
          ),
          for (final m in AppMode.values)
            ListTile(
              leading: Icon(m == mode.currentMode ? Icons.radio_button_checked : Icons.radio_button_off),
              title: Text(_modeLabels[m]!),
              selected: m == mode.currentMode,
              onTap: () {
                Navigator.pop(context);
                if (m != mode.currentMode) _switchMode(m);
              },
            ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.settings),
            title: const Text('设置'),
            onTap: () {
              Navigator.pop(context);
              Navigator.pushNamed(context, '/settings');
            },
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.logout, color: Colors.red),
            title: const Text('退出登录', style: TextStyle(color: Colors.red)),
            onTap: () {
              Navigator.pop(context);
              _logout();
            },
          ),
        ],
      ),
    );
  }
}
