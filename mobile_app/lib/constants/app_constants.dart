/// Development defaults for backend service URLs.
///
/// In production, set via `--dart-define` when building:
///   flutter build --dart-define=CLOUD_URL=https://api.example.com
class AppConstants {
  AppConstants._();

  static const String salesAssistantUrl = String.fromEnvironment(
    'SALES_ASSISTANT_URL',
    defaultValue: 'http://localhost:8004',
  );
  static const String cloudUrl = String.fromEnvironment(
    'CLOUD_URL',
    defaultValue: 'http://localhost:8000',
  );
  static const String opportunityUrl = String.fromEnvironment(
    'OPPORTUNITY_URL',
    defaultValue: 'http://localhost:8002',
  );
  static const String salesCoachUrl = String.fromEnvironment(
    'SALES_COACH_URL',
    defaultValue: 'http://localhost:8001',
  );
  static const String syncUrl = String.fromEnvironment(
    'SYNC_URL',
    defaultValue: 'http://localhost:8000',
  );
}
