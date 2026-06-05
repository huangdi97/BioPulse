import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:one_cloud_app/providers/auth_provider.dart';
import 'package:one_cloud_app/providers/mode_provider.dart';
import 'package:one_cloud_app/theme/app_theme.dart';
import 'package:one_cloud_app/screens/splash_screen.dart';
import 'package:one_cloud_app/screens/login_screen.dart';
import 'package:one_cloud_app/screens/home_screen.dart';
import 'package:one_cloud_app/screens/settings_screen.dart';
import 'package:one_cloud_app/screens/surgery/surgery_home_screen.dart';
import 'package:one_cloud_app/screens/opportunity/opportunity_list_screen.dart';
import 'package:one_cloud_app/screens/opportunity/opportunity_detail_screen.dart';
import 'package:one_cloud_app/screens/opportunity/opportunity_form_screen.dart';
import 'package:one_cloud_app/screens/management/management_dashboard_screen.dart';
import 'package:one_cloud_app/screens/management/compliance_record_screen.dart';
import 'package:one_cloud_app/screens/management/notification_screen.dart';
import 'package:one_cloud_app/screens/pharma/visit_list_screen.dart';
import 'package:one_cloud_app/screens/pharma/hcp_list_screen.dart';
import 'package:one_cloud_app/screens/pharma/compliance_screen.dart';
import 'package:one_cloud_app/screens/surgery/scan_screen.dart';
import 'package:one_cloud_app/screens/surgery/surgery_list_screen.dart';
import 'package:one_cloud_app/screens/surgery/surgery_detail_screen.dart';
import 'package:one_cloud_app/screens/surgery/surgery_form_screen.dart';
import 'package:one_cloud_app/screens/research/pi_search_screen.dart';
import 'package:one_cloud_app/screens/research/product_matching_screen.dart';
import 'package:one_cloud_app/screens/research/quotation_screen.dart';
import 'package:one_cloud_app/screens/sales_coach/training_list_screen.dart';
import 'package:one_cloud_app/screens/sales_coach/analysis_report_screen.dart';
import 'package:one_cloud_app/screens/sales_coach/recommendation_screen.dart';
import 'package:one_cloud_app/screens/register_screen.dart';
import 'package:one_cloud_app/screens/forgot_password_screen.dart';
import 'package:one_cloud_app/screens/onboarding_screen.dart';
import 'package:one_cloud_app/models/surgery.dart';

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
      case '/surgery_home':
        return MaterialPageRoute(builder: (_) => const SurgeryHomeScreen());
      case '/settings':
        return MaterialPageRoute(builder: (_) => const SettingsScreen());
      case '/opportunity_list':
        return MaterialPageRoute(builder: (_) => const OpportunityListScreen());
      case '/opportunity_detail':
        return MaterialPageRoute(builder: (_) => const OpportunityDetailScreen());
      case '/opportunity_form':
        return MaterialPageRoute(builder: (_) => const OpportunityFormScreen());
      case '/management':
        return MaterialPageRoute(builder: (_) => const ManagementDashboardScreen());
      case '/management/compliance':
        return MaterialPageRoute(builder: (_) => const ComplianceRecordScreen());
      case '/management/notifications':
        return MaterialPageRoute(builder: (_) => const NotificationScreen());
      case '/pharma/visit-list':
        return MaterialPageRoute(builder: (_) => const VisitListScreen());
      case '/pharma/hcp-list':
        return MaterialPageRoute(builder: (_) => const HcpListScreen());
      case '/pharma/compliance':
        return MaterialPageRoute(builder: (_) => const ComplianceScreen());
      case '/surgery/scan':
        return MaterialPageRoute(builder: (_) => const ScanScreen());
      case '/surgery/list':
        return MaterialPageRoute(builder: (_) => const SurgeryListScreen());
      case '/surgery/detail':
        return MaterialPageRoute(builder: (_) => SurgeryDetailScreen(surgery: settings.arguments as Surgery));
      case '/surgery/form':
        return MaterialPageRoute(builder: (_) => const SurgeryFormScreen());
      case '/research/pi-search':
        return MaterialPageRoute(builder: (_) => const PISearchScreen());
      case '/research/product-match':
        return MaterialPageRoute(builder: (_) => const ProductMatchingScreen());
      case '/research/quotation':
        return MaterialPageRoute(builder: (_) => const QuotationScreen());
      case '/coach/training-list':
        return MaterialPageRoute(builder: (_) => const TrainingListScreen());
      case '/coach/analysis-report':
        return MaterialPageRoute(builder: (_) => const AnalysisReportScreen());
      case '/coach/recommendation':
        return MaterialPageRoute(builder: (_) => const RecommendationScreen());
      case '/register':
        return MaterialPageRoute(builder: (_) => const RegisterScreen());
      case '/forgot_password':
        return MaterialPageRoute(builder: (_) => const ForgotPasswordScreen());
      case '/onboarding':
        return MaterialPageRoute(builder: (_) => const OnboardingScreen());
      default:
        return MaterialPageRoute(builder: (_) => const SplashScreen());
    }
  }
}
