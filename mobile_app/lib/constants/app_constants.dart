/// Development defaults for backend service URLs.
///
/// These are hardcoded for local development only.
/// In production, these values MUST be configured via environment variables
/// or runtime configuration (e.g. SharedPreferences).
class AppConstants {
  AppConstants._();

  static const String salesAssistantUrl = 'http://43.153.166.191:8004';
  static const String cloudUrl = 'http://43.153.166.191:8000';
  static const String opportunityUrl = 'http://43.153.166.191:8002';
  static const String salesCoachUrl = 'http://43.153.166.191:8001';
  static const String syncUrl = 'http://43.153.166.191:8000';
}
