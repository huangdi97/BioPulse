import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:biopulse_app/providers/auth_provider.dart';
import 'package:biopulse_app/services/sync_service.dart';

/// Splash screen displayed on app launch.
///
/// Checks for a valid authentication token and navigates to
/// [HomeScreen] if logged in, or [LoginScreen] if not.
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    await Future.delayed(const Duration(milliseconds: 800));

    if (!mounted) return;

    final auth = context.read<AuthProvider>();
    if (auth.isLoggedIn) {
      _triggerSync();
      final prefs = await SharedPreferences.getInstance();
      final launchMode = prefs.getString('launch_mode') ?? 'standard';
      final route = launchMode == 'surgery' ? '/surgery_home' : '/home';
      Navigator.pushReplacementNamed(context, route);
    } else {
      final prefs = await SharedPreferences.getInstance();
      final onboardingDone = prefs.getBool('onboarding_done') ?? false;
      final route = onboardingDone ? '/login' : '/onboarding';
      Navigator.pushReplacementNamed(context, route);
    }
  }

  Future<void> _triggerSync() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs.getString('backend_urls');
      if (saved == null) return;
      final urls = Map<String, String>.from(jsonDecode(saved) as Map);
      context.read<SyncService>().pullAll(urls);
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.cloud_outlined,
              size: 80,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: 24),
            Text(
              'BioPulse',
              style: theme.textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: theme.colorScheme.primary,
              ),
            ),
            const SizedBox(height: 32),
            CircularProgressIndicator(color: theme.colorScheme.primary),
          ],
        ),
      ),
    );
  }
}
