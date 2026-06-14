import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:biopulse_app/services/api_client.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  bool _isLoading = false;

  @override
  void dispose() {
    _usernameController.dispose();
    super.dispose();
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isLoading = true);
    try {
      final apiClient = context.read<ApiClient>();
      final response = await apiClient.post(
        '/auth/forgot-password',
        data: {'username': _usernameController.text.trim()},
      );
      if (!mounted) return;
      if (response.isSuccess) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('密码重置邮件已发送，请查收'), backgroundColor: Colors.green),
        );
        Navigator.pushReplacementNamed(context, '/login');
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(response.message.isNotEmpty ? response.message : '请求失败，请重试')),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('请求失败: $e')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('忘记密码'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pushReplacementNamed(context, '/login'),
        ),
      ),
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
                  Icon(Icons.lock_reset, size: 64, color: theme.colorScheme.primary),
                  const SizedBox(height: 16),
                  Text('忘记密码', textAlign: TextAlign.center,
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold, color: theme.colorScheme.primary,
                    )),
                  const SizedBox(height: 8),
                  Text('请输入您的用户名，我们会发送密码重置链接到您的注册邮箱',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.bodyMedium?.copyWith(color: Colors.grey[600])),
                  const SizedBox(height: 40),
                  TextFormField(
                    controller: _usernameController,
                    decoration: const InputDecoration(
                      labelText: '用户名', prefixIcon: Icon(Icons.person_outline)),
                    validator: (v) => v == null || v.trim().isEmpty ? '请输入用户名' : null,
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: _isLoading ? null : _handleSubmit,
                    child: _isLoading
                        ? const SizedBox(height: 20, width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : const Text('提交'),
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
