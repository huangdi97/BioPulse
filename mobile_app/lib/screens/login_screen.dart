import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:biopulse_app/providers/auth_provider.dart';
import 'package:biopulse_app/providers/mode_provider.dart';
import 'package:biopulse_app/services/sync_service.dart';

/// Login screen with username/password fields and loading state.
///
/// Displays validation errors and navigates to [HomeScreen]
/// upon successful authentication.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;
  AppMode _selectedMode = AppMode.pharma;

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

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
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

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;

    final auth = context.read<AuthProvider>();
    final success = await auth.login(
      _usernameController.text.trim(),
      _passwordController.text,
      scope: _scopeFromMode(_selectedMode),
    );

    if (success && mounted) {
      _triggerSync();
      final prefs = await SharedPreferences.getInstance();
      final launchMode = prefs.getString('launch_mode') ?? 'standard';
      final route = launchMode == 'surgery' ? '/surgery_home' : '/home';
      Navigator.pushReplacementNamed(context, route);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Icon(
                    Icons.cloud_outlined,
                    size: 64,
                    color: theme.colorScheme.primary,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'BioPulse',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '欢迎登录',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.bodyLarge?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                  const SizedBox(height: 40),
                  Consumer<AuthProvider>(
                    builder: (context, auth, _) {
                      if (auth.error != null) {
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 16),
                          child: Text(
                            auth.error!,
                            style: TextStyle(color: theme.colorScheme.error),
                            textAlign: TextAlign.center,
                          ),
                        );
                      }
                      return const SizedBox.shrink();
                    },
                  ),
                  TextFormField(
                    controller: _usernameController,
                    decoration: const InputDecoration(
                      labelText: '用户名',
                      prefixIcon: Icon(Icons.person_outline),
                    ),
                    validator: (v) =>
                        v == null || v.trim().isEmpty ? '请输入用户名' : null,
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _passwordController,
                    obscureText: _obscurePassword,
                    decoration: InputDecoration(
                      labelText: '密码',
                      prefixIcon: const Icon(Icons.lock_outline),
                      suffixIcon: IconButton(
                        icon: Icon(
                          _obscurePassword
                              ? Icons.visibility_off
                              : Icons.visibility,
                        ),
                        onPressed: () =>
                            setState(() => _obscurePassword = !_obscurePassword),
                      ),
                    ),
                    validator: (v) =>
                        v == null || v.isEmpty ? '请输入密码' : null,
                  ),
                  const SizedBox(height: 16),
                  DropdownButtonFormField<AppMode>(
                    value: _selectedMode,
                    decoration: const InputDecoration(
                      labelText: '登录模式',
                      prefixIcon: Icon(Icons.swap_horiz),
                    ),
                    items: const [
                      DropdownMenuItem(value: AppMode.pharma, child: Text('医药模式')),
                      DropdownMenuItem(value: AppMode.surgery, child: Text('手术模式')),
                      DropdownMenuItem(value: AppMode.opportunity, child: Text('商机模式')),
                      DropdownMenuItem(value: AppMode.salesCoach, child: Text('销售教练模式')),
                      DropdownMenuItem(value: AppMode.research, child: Text('研究模式')),
                    ],
                    onChanged: (v) {
                      if (v != null) setState(() => _selectedMode = v);
                    },
                  ),
                  const SizedBox(height: 24),
                  Consumer<AuthProvider>(
                    builder: (context, auth, _) {
                      return ElevatedButton(
                        onPressed: auth.isLoading ? null : _handleLogin,
                        child: auth.isLoading
                            ? const SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Text('登录'),
                      );
                    },
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
