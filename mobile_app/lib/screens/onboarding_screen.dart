import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final _controller = PageController();
  int _currentPage = 0;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _completeOnboarding() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('onboarding_done', true);
    if (!mounted) return;
    Navigator.pushReplacementNamed(context, '/login');
  }

  void _onSkip() => _completeOnboarding();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Align(
              alignment: Alignment.topRight,
              child: TextButton(
                onPressed: _onSkip,
                child: Text('跳过', style: TextStyle(color: theme.colorScheme.primary)),
              ),
            ),
            Expanded(
              child: PageView(
                controller: _controller,
                onPageChanged: (page) => setState(() => _currentPage = page),
                children: [
                  _buildPage(
                    icon: Icons.cloud_done_outlined,
                    title: '欢迎使用 One Cloud App',
                    description: '一站式云端工作平台，\n助力您的业务高效运转',
                    theme: theme,
                  ),
                  _buildPage(
                    icon: Icons.apps_outlined,
                    title: '功能概览',
                    description: '医药拜访、手术管理、商机跟进、\n销售教练、科研匹配\n多模式自由切换',
                    theme: theme,
                  ),
                  _buildPage(
                    icon: Icons.rocket_launch_outlined,
                    title: '开始使用',
                    description: '一切准备就绪，\n立即开始您的云端之旅',
                    theme: theme,
                    isLast: true,
                    onGetStarted: _completeOnboarding,
                  ),
                ],
              ),
            ),
            _buildIndicator(theme),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildPage({
    required IconData icon,
    required String title,
    required String description,
    required ThemeData theme,
    bool isLast = false,
    VoidCallback? onGetStarted,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 100, color: theme.colorScheme.primary),
          const SizedBox(height: 48),
          Text(title, textAlign: TextAlign.center,
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold, color: theme.colorScheme.primary,
            )),
          const SizedBox(height: 16),
          Text(description, textAlign: TextAlign.center,
            style: theme.textTheme.bodyLarge?.copyWith(color: Colors.grey[600], height: 1.6)),
          if (isLast) ...[
            const SizedBox(height: 48),
            ElevatedButton(
              onPressed: onGetStarted,
              child: const Text('开始使用'),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildIndicator(ThemeData theme) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(3, (index) {
        final isActive = index == _currentPage;
        return AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          margin: const EdgeInsets.symmetric(horizontal: 4),
          width: isActive ? 24 : 8,
          height: 8,
          decoration: BoxDecoration(
            color: isActive ? theme.colorScheme.primary : Colors.grey[300],
            borderRadius: BorderRadius.circular(4),
          ),
        );
      }),
    );
  }
}
