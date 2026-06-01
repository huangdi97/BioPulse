import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:one_cloud_app/providers/auth_provider.dart';
import 'package:one_cloud_app/providers/mode_provider.dart';
import 'package:one_cloud_app/screens/settings_screen.dart';
import 'package:one_cloud_app/screens/pharma/visit_list_screen.dart';
import 'package:one_cloud_app/screens/pharma/hcp_list_screen.dart';
import 'package:one_cloud_app/screens/pharma/compliance_screen.dart';
import 'package:one_cloud_app/screens/surgery/surgery_list_screen.dart';
import 'package:one_cloud_app/screens/research/pi_search_screen.dart';
import 'package:one_cloud_app/screens/research/product_matching_screen.dart';
import 'package:one_cloud_app/screens/research/quotation_screen.dart';

/// Main home screen with mode switching, bottom navigation, and drawer.
///
/// Pharma mode shows: Visit / HCP / Compliance / Settings
/// Research mode shows: PI Search / Product / Quote / Settings
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  void _onItemTapped(int index) {
    setState(() => _currentIndex = index);
  }

  void _switchMode() {
    context.read<ModeProvider>().toggleMode();
    setState(() => _currentIndex = 0);
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

  @override
  Widget build(BuildContext context) {
    final mode = context.watch<ModeProvider>();
    final auth = context.watch<AuthProvider>();
    final isPharma = mode.isPharmaMode;

    final pages = isPharma ? _pharmaPages : _researchPages;

    return Scaffold(
      appBar: AppBar(
        title: Text(isPharma ? '销售助手' : '科研助手'),
        actions: [
          IconButton(
            icon: Icon(isPharma ? Icons.science : Icons.medication),
            tooltip: isPharma ? '切换到科研模式' : '切换到销售模式',
            onPressed: _switchMode,
          ),
        ],
      ),
      drawer: _buildDrawer(context, auth, mode),
      body: pages[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: _onItemTapped,
        destinations: isPharma ? _pharmaDestinations : _researchDestinations,
      ),
    );
  }

  List<Widget> get _pharmaPages => [
        const VisitListScreen(),
        const HcpListScreen(),
        const ComplianceScreen(),
        const SurgeryListScreen(),
        const SettingsScreen(),
      ];

  List<Widget> get _researchPages => [
        const PISearchScreen(),
        const ProductMatchingScreen(),
        const QuotationScreen(),
        const SettingsScreen(),
      ];

  List<NavigationDestination> get _pharmaDestinations => [
        const NavigationDestination(
          icon: Icon(Icons.calendar_today_outlined),
          selectedIcon: Icon(Icons.calendar_today),
          label: '拜访',
        ),
        const NavigationDestination(
          icon: Icon(Icons.people_outline),
          selectedIcon: Icon(Icons.people),
          label: 'HCP',
        ),
        const NavigationDestination(
          icon: Icon(Icons.verified_outlined),
          selectedIcon: Icon(Icons.verified),
          label: '合规',
        ),
        const NavigationDestination(
          icon: Icon(Icons.local_hospital_outlined),
          selectedIcon: Icon(Icons.local_hospital),
          label: '手术',
        ),
        const NavigationDestination(
          icon: Icon(Icons.settings_outlined),
          selectedIcon: Icon(Icons.settings),
          label: '设置',
        ),
      ];

  List<NavigationDestination> get _researchDestinations => [
        const NavigationDestination(
          icon: Icon(Icons.search_outlined),
          selectedIcon: Icon(Icons.search),
          label: 'PI搜索',
        ),
        const NavigationDestination(
          icon: Icon(Icons.mediation_outlined),
          selectedIcon: Icon(Icons.mediation),
          label: '匹配',
        ),
        const NavigationDestination(
          icon: Icon(Icons.request_quote_outlined),
          selectedIcon: Icon(Icons.request_quote),
          label: '报价',
        ),
        const NavigationDestination(
          icon: Icon(Icons.settings_outlined),
          selectedIcon: Icon(Icons.settings),
          label: '设置',
        ),
      ];

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
                const CircleAvatar(
                  radius: 28,
                  child: Icon(Icons.person, size: 32),
                ),
                const SizedBox(height: 12),
                Text(
                  auth.user?['username'] as String? ?? '用户',
                  style: const TextStyle(color: Colors.white, fontSize: 18),
                ),
                Text(
                  mode.isPharmaMode ? '销售助手模式' : '科研模式',
                  style: TextStyle(color: Colors.white.withValues(alpha: 0.8)),
                ),
              ],
            ),
          ),
          ListTile(
            leading: const Icon(Icons.swap_horiz),
            title: Text(mode.isPharmaMode ? '切换到科研模式' : '切换到销售模式'),
            onTap: () {
              _switchMode();
              Navigator.pop(context);
            },
          ),
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


