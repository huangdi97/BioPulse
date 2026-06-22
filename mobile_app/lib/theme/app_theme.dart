import 'package:flutter/material.dart';
import 'package:biopulse_app/providers/mode_provider.dart';

/// Centralized app theme definition.
///
/// Provides light and dark color schemes for pharma (blue),
/// research (green), and admin (purple) modes.
class AppTheme {
  AppTheme._();

  // Pharma mode – blue palette.
  static const Color _pharmaPrimary = Color(0xFF1565C0);
  static const Color _pharmaSecondary = Color(0xFF42A5F5);
  static const Color _pharmaSurface = Color(0xFFF5F9FF);

  // Research mode – green palette.
  static const Color _researchPrimary = Color(0xFF2E7D32);
  static const Color _researchSecondary = Color(0xFF66BB6A);
  static const Color _researchSurface = Color(0xFFF5FFF5);

  // Admin mode – purple palette.
  static const Color _adminPrimary = Color(0xFF6A1B9A);
  static const Color _adminSecondary = Color(0xFFAB47BC);
  static const Color _adminSurface = Color(0xFFFAF5FF);

  // Neutral.
  static const Color _error = Color(0xFFD32F2F);
  static const Color _onPrimary = Colors.white;

  /// Return a [ThemeData] based on [mode], [brightness], and [isAdmin].
  static ThemeData getTheme({
    AppMode mode = AppMode.pharma,
    Brightness brightness = Brightness.light,
    bool isAdmin = false,
  }) {
    final Color primary;
    final Color secondary;
    final Color surface;

    if (isAdmin) {
      primary = _adminPrimary;
      secondary = _adminSecondary;
      surface = _adminSurface;
    } else if (mode == AppMode.pharma) {
      primary = _pharmaPrimary;
      secondary = _pharmaSecondary;
      surface = _pharmaSurface;
    } else {
      primary = _researchPrimary;
      secondary = _researchSecondary;
      surface = _researchSurface;
    }

    final isDark = brightness == Brightness.dark;
    final ColorScheme colorScheme;

    if (isDark) {
      colorScheme = ColorScheme.dark(
        primary: primary,
        secondary: secondary,
        surface: surface.withValues(alpha: 0.1),
        error: _error,
        onPrimary: _onPrimary,
      );
    } else {
      colorScheme = ColorScheme.light(
        primary: primary,
        secondary: secondary,
        surface: surface,
        error: _error,
        onPrimary: _onPrimary,
      );
    }

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      appBarTheme: AppBarTheme(
        backgroundColor: colorScheme.primary,
        foregroundColor: _onPrimary,
        elevation: 0,
        centerTitle: true,
      ),
      navigationBarTheme: NavigationBarThemeData(
        indicatorColor: colorScheme.secondary.withValues(alpha: 0.3),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: colorScheme.primary,
            );
          }
          return TextStyle(fontSize: 12, color: Colors.grey);
        }),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: colorScheme.primary,
          foregroundColor: _onPrimary,
          minimumSize: const Size(double.infinity, 48),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
      cardTheme: CardThemeData(
        elevation: 1,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }
}
