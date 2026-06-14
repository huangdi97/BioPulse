import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:biopulse_app/providers/auth_provider.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _handleRegister() async {
    if (!_formKey.currentState!.validate()) return;
    final auth = context.read<AuthProvider>();
    final success = await auth.register(
      _usernameController.text.trim(),
      _passwordController.text,
    );
    if (success && mounted) {
      Navigator.pushReplacementNamed(context, '/home');
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
                  Icon(Icons.cloud_outlined, size: 64, color: theme.colorScheme.primary),
                  const SizedBox(height: 16),
                  Text('创建账号', textAlign: TextAlign.center,
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold, color: theme.colorScheme.primary,
                    )),
                  const SizedBox(height: 8),
                  Text('注册新账号', textAlign: TextAlign.center,
                    style: theme.textTheme.bodyLarge?.copyWith(color: Colors.grey[600])),
                  const SizedBox(height: 40),
                  Consumer<AuthProvider>(
                    builder: (context, auth, _) {
                      if (auth.error != null) {
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 16),
                          child: Text(auth.error!,
                            style: TextStyle(color: theme.colorScheme.error),
                            textAlign: TextAlign.center),
                        );
                      }
                      return const SizedBox.shrink();
                    },
                  ),
                  TextFormField(
                    controller: _usernameController,
                    decoration: const InputDecoration(
                      labelText: '用户名', prefixIcon: Icon(Icons.person_outline)),
                    validator: (v) => v == null || v.trim().isEmpty ? '请输入用户名' : null,
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _passwordController,
                    obscureText: _obscurePassword,
                    decoration: InputDecoration(
                      labelText: '密码',
                      prefixIcon: const Icon(Icons.lock_outline),
                      suffixIcon: IconButton(
                        icon: Icon(_obscurePassword ? Icons.visibility_off : Icons.visibility),
                        onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                      ),
                    ),
                    validator: (v) {
                      if (v == null || v.isEmpty) return '请输入密码';
                      if (v.length < 6) return '密码长度不能少于6位';
                      return null;
                    },
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _confirmPasswordController,
                    obscureText: _obscureConfirmPassword,
                    decoration: InputDecoration(
                      labelText: '确认密码',
                      prefixIcon: const Icon(Icons.lock_outline),
                      suffixIcon: IconButton(
                        icon: Icon(_obscureConfirmPassword ? Icons.visibility_off : Icons.visibility),
                        onPressed: () => setState(() => _obscureConfirmPassword = !_obscureConfirmPassword),
                      ),
                    ),
                    validator: (v) {
                      if (v == null || v.isEmpty) return '请确认密码';
                      if (v != _passwordController.text) return '两次输入的密码不一致';
                      return null;
                    },
                  ),
                  const SizedBox(height: 24),
                  Consumer<AuthProvider>(
                    builder: (context, auth, _) {
                      return ElevatedButton(
                        onPressed: auth.isLoading ? null : _handleRegister,
                        child: auth.isLoading
                            ? const SizedBox(height: 20, width: 20,
                                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                            : const Text('注册'),
                      );
                    },
                  ),
                  const SizedBox(height: 16),
                  TextButton(
                    onPressed: () => Navigator.pushReplacementNamed(context, '/login'),
                    child: Text('已有账号？立即登录', style: TextStyle(color: theme.colorScheme.primary)),
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
