import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class PushService {
  bool _initialized = false;
  String? _deviceToken;

  bool get isInitialized => _initialized;
  String? get deviceToken => _deviceToken;

  Future<void> initialize() async {
    if (_initialized) return;
    try {
      final prefs = await SharedPreferences.getInstance();
      _deviceToken = prefs.getString('push_device_token');
      if (_deviceToken == null) {
        _deviceToken = _generateLocalToken();
        await prefs.setString('push_device_token', _deviceToken!);
      }
      _initialized = true;
      debugPrint('PushService initialized with token: $_deviceToken');
    } catch (e) {
      _initialized = true;
      _deviceToken = _generateLocalToken();
      debugPrint('PushService initialized (fallback): $e');
    }
  }

  Future<void> registerForPush() async {
    await initialize();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('push_registered', true);
    debugPrint('PushService: registered for push notifications');
  }

  Future<bool> isRegistered() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool('push_registered') ?? false;
  }

  Future<void> unregister() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('push_device_token');
    await prefs.remove('push_registered');
    _deviceToken = null;
    _initialized = false;
  }

  String _generateLocalToken() {
    final now = DateTime.now().millisecondsSinceEpoch;
    return 'local_push_token_${now}_${now % 10000}';
  }
}