import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:one_cloud_app/app.dart';
import 'package:one_cloud_app/services/auth_service.dart';
import 'package:one_cloud_app/services/database_service.dart';
import 'package:one_cloud_app/services/api_client.dart';
import 'package:one_cloud_app/providers/auth_provider.dart';
import 'package:one_cloud_app/providers/mode_provider.dart';

/// Application entry point.
///
/// Initializes Flutter bindings, local database, and services
/// before launching the [App] widget tree with providers.
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final databaseService = DatabaseService();
  await databaseService.initDatabase();

  final authService = AuthService();
  final apiClient = ApiClient(
    baseUrl: 'https://api.example.com',
    authService: authService,
  );
  authService.setApiClient(apiClient);

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
      ],
      child: const App(),
    ),
  );
}
