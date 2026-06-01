import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:one_cloud_app/providers/auth_provider.dart';
import 'package:one_cloud_app/providers/mode_provider.dart';
import 'package:one_cloud_app/theme/app_theme.dart';
import 'package:one_cloud_app/screens/splash_screen.dart';
import 'package:one_cloud_app/screens/login_screen.dart';
import 'package:one_cloud_app/screens/home_screen.dart';
import 'package:one_cloud_app/screens/settings_screen.dart';

/// Root MaterialApp widget with provider tree and route configuration.
///
/// Wraps the app in [MultiProvider] with [AuthProvider] and [ModeProvider],
/// and configures theming based on the current mode and brightness.
class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer2<AuthProvider, ModeProvider>(
      builder: (context, auth, mode, _) {
        return MaterialApp(
          title: 'One Cloud App',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.getTheme(mode: mode.currentMode),
          darkTheme: AppTheme.getTheme(
            mode: mode.currentMode,
            brightness: Brightness.dark,
          ),
          themeMode: ThemeMode.system,
          initialRoute: '/splash',
          onGenerateRoute: _onGenerateRoute,
        );
      },
    );
  }

  Route<dynamic>? _onGenerateRoute(RouteSettings settings) {
    switch (settings.name) {
      case '/splash':
        return MaterialPageRoute(builder: (_) => const SplashScreen());
      case '/login':
        return MaterialPageRoute(builder: (_) => const LoginScreen());
      case '/home':
        return MaterialPageRoute(builder: (_) => const HomeScreen());
      case '/settings':
        return MaterialPageRoute(builder: (_) => const SettingsScreen());
      default:
        return MaterialPageRoute(builder: (_) => const SplashScreen());
    }
  }
}
