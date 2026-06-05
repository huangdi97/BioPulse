import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:one_cloud_app/app.dart';
import 'package:one_cloud_app/services/auth_service.dart';
import 'package:one_cloud_app/services/database_service.dart';
import 'package:one_cloud_app/services/api_client.dart';
import 'package:one_cloud_app/services/sync_service.dart';
import 'package:one_cloud_app/providers/auth_provider.dart';
import 'package:one_cloud_app/providers/mode_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final databaseService = DatabaseService();
  await databaseService.initDatabase();

  final authService = AuthService();

  final prefs = await SharedPreferences.getInstance();
  final savedUrls = prefs.getString('backend_urls');
  const defaultUrls = {
    'sales_assistant': 'http://43.153.166.191:8004',
    'cloud': 'http://43.153.166.191:8000',
    'opportunity': 'http://43.153.166.191:8002',
    'sales_coach': 'http://43.153.166.191:8001',
    'sync': 'http://43.153.166.191:8000',
  };
  final urls = savedUrls != null
      ? Map<String, String>.from(jsonDecode(savedUrls) as Map)
      : defaultUrls;

  final apiClient = ApiClient(
    baseUrl: urls['cloud'] ?? 'https://api.example.com',
    authService: authService,
  );
  authService.setApiClient(apiClient);

  final multiBackendClient = MultiBackendApiClient(
    authService: authService,
    backends: urls,
    defaultName: 'cloud',
  );

  final syncService = SyncService(
    databaseService,
    Dio(BaseOptions(connectTimeout: const Duration(seconds: 10))),
  );

  final authProvider = AuthProvider(authService);
  final modeProvider = ModeProvider();

  await authProvider.init();
  await modeProvider.init();

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider.value(value: authProvider),
        ChangeNotifierProvider.value(value: modeProvider),
        Provider.value(value: databaseService),
        Provider.value(value: authService),
        Provider.value(value: apiClient),
        Provider.value(value: multiBackendClient),
        Provider.value(value: syncService),
      ],
      child: const App(),
    ),
  );
}
