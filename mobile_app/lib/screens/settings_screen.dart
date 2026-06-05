import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:one_cloud_app/services/database_service.dart';
import 'package:one_cloud_app/services/api_client.dart';
import 'package:provider/provider.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _controllers = <String, TextEditingController>{};
  bool _isLoading = false;
  String _launchMode = 'standard';

  static const _backendUrlsKey = 'backend_urls';
  static const _defaultUrl = 'https://api.example.com';

  static const _backendLabels = {
    'sales_assistant': '医药助手',
    'cloud': '云服务',
    'opportunity': '商机',
    'sales_coach': '销售教练',
    'sync': '数据同步',
  };

  @override
  void dispose() {
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    for (final key in _backendLabels.keys) {
      _controllers[key] = TextEditingController();
    }
    _loadUrls();
    _loadLaunchMode();
  }

  Future<void> _loadLaunchMode() async {
    final prefs = await SharedPreferences.getInstance();
    if (mounted) {
      setState(() {
        _launchMode = prefs.getString('launch_mode') ?? 'standard';
      });
    }
  }

  Future<void> _saveLaunchMode(String value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('launch_mode', value);
    if (mounted) setState(() => _launchMode = value);
  }

  Future<void> _loadUrls() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_backendUrlsKey);
    final urls = saved != null
        ? Map<String, String>.from(jsonDecode(saved) as Map)
        : <String, String>{};
    for (final key in _backendLabels.keys) {
      _controllers[key]?.text = urls[key] ?? _defaultUrl;
    }
    if (mounted) {
      final multiClient = context.read<MultiBackendApiClient>();
      for (final entry in urls.entries) {
        multiClient.addBackend(entry.key, entry.value);
      }
    }
  }

  Future<void> _saveUrls() async {
    final urls = <String, String>{};
    for (final key in _backendLabels.keys) {
      urls[key] = _controllers[key]?.text.trim() ?? _defaultUrl;
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_backendUrlsKey, jsonEncode(urls));
    if (mounted) {
      final multiClient = context.read<MultiBackendApiClient>();
      for (final entry in urls.entries) {
        multiClient.addBackend(entry.key, entry.value);
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('服务器地址已保存')),
      );
    }
  }

  Future<void> _clearCache() async {
    setState(() => _isLoading = true);
    try {
      final db = context.read<DatabaseService>();
      for (final v in await db.getVisits()) {
        if (v.id != null) await db.deleteVisit(v.id!);
      }
      for (final s in await db.getSurgeries()) {
        if (s.id != null) await db.deleteSurgery(s.id!);
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('缓存已清理')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('设置')),
      body: Builder(
        builder: (context) {
          final multiClient = context.read<MultiBackendApiClient>();
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('服务器配置',
                          style: theme.textTheme.titleMedium
                              ?.copyWith(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 12),
                      for (final name in multiClient.backendNames)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: TextField(
                            controller: _controllers[name],
                            decoration: InputDecoration(
                              labelText: _backendLabels[name] ?? name,
                              hintText: _defaultUrl,
                              prefixIcon: const Icon(Icons.link),
                            ),
                            keyboardType: TextInputType.url,
                          ),
                        ),
                      Align(
                        alignment: Alignment.centerRight,
                        child: ElevatedButton.icon(
                          onPressed: _saveUrls,
                          icon: const Icon(Icons.save),
                          label: const Text('保存'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('缓存管理',
                          style: theme.textTheme.titleMedium
                              ?.copyWith(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: _isLoading ? null : _clearCache,
                          icon: _isLoading
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                )
                              : const Icon(Icons.delete_sweep),
                          label: const Text('清理本地数据'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('启动模式',
                          style: theme.textTheme.titleMedium
                              ?.copyWith(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        value: _launchMode,
                        decoration: const InputDecoration(
                          labelText: '启动后进入',
                          prefixIcon: Icon(Icons.launch),
                        ),
                        items: const [
                          DropdownMenuItem(
                              value: 'standard', child: Text('标准模式（模式切换页）')),
                          DropdownMenuItem(
                              value: 'surgery',
                              child: Text('跟台模式（直接进入跟台首页）')),
                        ],
                        onChanged: (v) {
                          if (v != null) _saveLaunchMode(v);
                        },
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('关于',
                          style: theme.textTheme.titleMedium
                              ?.copyWith(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 12),
                      _infoRow('应用名称', 'One Cloud App'),
                      _infoRow('版本', '1.0.0+1'),
                      _infoRow('构建号', '1'),
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: Colors.grey[600])),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}
