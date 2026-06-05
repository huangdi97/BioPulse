import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:one_cloud_app/services/sync_service.dart';

class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key});
  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen>
    with SingleTickerProviderStateMixin {
  final _scanResults = <String>[];
  final _imagePicker = ImagePicker();
  late AnimationController _animController;
  late Animation<double> _scanLineAnim;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
    _scanLineAnim = Tween<double>(begin: 0, end: 0.8).animate(
      CurvedAnimation(parent: _animController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  void _simulateScan() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('手动输入条码'),
        content: const Text('请输入或粘贴产品条码/二维码内容'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('取消')),
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('模拟扫码'),
          ),
        ],
      ),
    );
  }

  Future<void> _takePhoto() async {
    try {
      final photo = await _imagePicker.pickImage(source: ImageSource.camera);
      if (photo != null) {
        final timestamp = DateTime.now()
            .toIso8601String()
            .replaceAll(RegExp(r'[T:.]'), '-')
            .substring(0, 19);
        setState(() => _scanResults.add('[图片] 拍摄于 $timestamp'));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('拍照失败，请检查相机权限')),
        );
      }
    }
  }

  Future<void> _onRefresh() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs.getString('backend_urls');
      String? baseUrl;
      if (saved != null) {
        final urls = Map<String, String>.from(jsonDecode(saved) as Map);
        baseUrl = urls['assistant'] ?? urls['sales_assistant'];
      }
      if (baseUrl != null) {
        await context.read<SyncService>().pullSurgeries(baseUrl);
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('同步服务暂不可用')),
        );
      }
    }
  }

  void _confirmAndReturn() {
    final combined = _scanResults.join('\n');
    Navigator.pop(context, combined);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('扫码'),
        actions: [
          TextButton(
            onPressed: _scanResults.isNotEmpty ? _confirmAndReturn : null,
            child: const Text('完成'),
          ),
        ],
      ),
      body: Column(
        children: [
          Container(
            height: 260,
            color: Colors.black87,
            child: Stack(
              alignment: Alignment.center,
              children: [
                Container(
                  width: 220,
                  height: 180,
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.green, width: 2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                AnimatedBuilder(
                  animation: _scanLineAnim,
                  builder: (ctx, _) {
                    return Positioned(
                      top: 40 + _scanLineAnim.value * 160,
                      child: Container(
                        width: 200,
                        height: 2,
                        color: Colors.green.withValues(alpha: 0.8),
                      ),
                    );
                  },
                ),
                Positioned(
                  bottom: 16,
                  child: Text(
                    '将条码置于取景框内',
                    style: TextStyle(color: Colors.white70, fontSize: 12),
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _simulateScan,
                    icon: const Icon(Icons.qr_code_scanner),
                    label: const Text('模拟扫码'),
                  ),
                ),
                const SizedBox(width: 12),
                ElevatedButton.icon(
                  onPressed: _takePhoto,
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('拍照'),
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                const Text('扫码记录',
                    style: TextStyle(fontWeight: FontWeight.w600)),
                const Spacer(),
                Text('${_scanResults.length} 条',
                    style: TextStyle(color: Colors.grey[600])),
              ],
            ),
          ),
          Expanded(
            child: RefreshIndicator(
              onRefresh: _onRefresh,
              child: _scanResults.isEmpty
                  ? ListView(
                      children: [
                        SizedBox(
                          height: 200,
                          child: Center(
                            child: Text('暂无扫码记录',
                                style: TextStyle(color: Colors.grey[500])),
                          ),
                        ),
                      ],
                    )
                  : ListView.builder(
                      itemCount: _scanResults.length,
                      itemBuilder: (_, i) => ListTile(
                        leading: Icon(
                          _scanResults[i].startsWith('[图片]')
                              ? Icons.image
                              : Icons.qr_code,
                          color: theme.colorScheme.primary,
                        ),
                        title: Text(_scanResults[i], style: const TextStyle(fontSize: 13)),
                        dense: true,
                      ),
                    ),
            ),
          ),
        ],
      ),
    );
  }
}
