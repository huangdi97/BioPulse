class ComplianceResult {
  final bool passed;
  final List<String> violations;
  final List<String> warnings;
  final String riskLevel;
  final int score;

  const ComplianceResult({
    required this.passed,
    this.violations = const [],
    this.warnings = const [],
    this.riskLevel = 'low',
    this.score = 100,
  });
}
