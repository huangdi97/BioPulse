// ==========================================
// 一云四端 Design System — Flutter Tokens
// 来源: design-tokens/tokens.json (单一源)
// 生成方式: 手动转译，以 tokens.json 为准
// ==========================================

import 'package:flutter/material.dart';

class DesignTokens {
  // Brand
  static const Color brand = Color(0xFF0F62FE);
  static const Color brandHover = Color(0xFF0353E9);
  static const Color brandActive = Color(0xFF002D9C);
  static const Color brandLight = Color(0xFFEDF5FF);

  // Mode
  static const Color modePharma = Color(0xFF0F62FE);
  static const Color modeResearch = Color(0xFF8B5CF6);
  static const Color modeWarn = Color(0xFFF59E0B);
  static const Color modePass = Color(0xFF10B981);

  // Status
  static const Color success = Color(0xFF24A148);
  static const Color error = Color(0xFFDA1E28);
  static const Color warning = Color(0xFFF1C21B);
  static const Color info = Color(0xFF0F62FE);

  // Neutral
  static const Color white = Color(0xFFFFFFFF);
  static const Color gray10 = Color(0xFFF4F4F4);
  static const Color gray20 = Color(0xFFE0E0E0);
  static const Color gray30 = Color(0xFFC6C6C6);
  static const Color gray50 = Color(0xFF8D8D8D);
  static const Color gray60 = Color(0xFF6F6F6F);
  static const Color gray70 = Color(0xFF525252);
  static const Color gray90 = Color(0xFF262626);
  static const Color gray100 = Color(0xFF161616);

  // Text
  static const Color textPrimary = Color(0xFF161616);
  static const Color textSecondary = Color(0xFF525252);
  static const Color textPlaceholder = Color(0xFF6F6F6F);
  static const Color textDisabled = Color(0xFF8D8D8D);
  static const Color textInverse = Color(0xFFFFFFFF);

  // Surface
  static const Color surfacePage = Color(0xFFFFFFFF);
  static const Color surfaceCard = Color(0xFFFFFFFF);
  static const Color surfaceCardAlt = Color(0xFFF4F4F4);
  static const Color surfaceHover = Color(0xFFE8E8E8);
  static const Color surfaceSelected = Color(0xFFEDF5FF);

  // Border
  static const Color borderDefault = Color(0xFFE0E0E0);
  static const Color borderSubtle = Color(0xFFC6C6C6);
  static const Color borderInput = Color(0xFFF4F4F4);
  static const Color borderFocus = Color(0xFF0F62FE);
  static const Color borderError = Color(0xFFDA1E28);

  // Spacing
  static const double spaceXs = 4.0;
  static const double spaceSm = 8.0;
  static const double spaceMd = 16.0;
  static const double spaceLg = 24.0;
  static const double spaceXl = 32.0;
  static const double spaceXxl = 48.0;
  static const double spaceXxxl = 64.0;

  // Border Radius
  static const double radiusNone = 0.0;
  static const double radiusSm = 4.0;
  static const double radiusMd = 6.0;
  static const double radiusLg = 8.0;
  static const double radiusXl = 12.0;
  static const double radiusPill = 9999.0;

  // Typography
  static const String fontPrimary = 'Inter';
  static const String fontMono = 'JetBrainsMono';

  // Pre-built TextStyles
  static const TextStyle display = TextStyle(
    fontSize: 48,
    fontWeight: FontWeight.w600,
    height: 1.1,
    letterSpacing: -1.2,
  );

  static const TextStyle h1 = TextStyle(
    fontSize: 32,
    fontWeight: FontWeight.w600,
    height: 1.25,
    letterSpacing: -0.6,
  );

  static const TextStyle h2 = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.w600,
    height: 1.33,
    letterSpacing: -0.3,
  );

  static const TextStyle h3 = TextStyle(
    fontSize: 20,
    fontWeight: FontWeight.w500,
    height: 1.4,
  );

  static const TextStyle body = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.w400,
    height: 1.5,
  );

  static const TextStyle bodySm = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w400,
    height: 1.4,
    letterSpacing: 0.16,
  );

  static const TextStyle caption = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w500,
    height: 1.33,
    letterSpacing: 0.32,
  );

  static const TextStyle label = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w600,
    height: 1.33,
    letterSpacing: 0.32,
  );

  static const TextStyle mono = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w400,
    height: 1.4,
    fontFamily: fontMono,
  );

  // Theme
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      fontFamily: fontPrimary,
      colorScheme: const ColorScheme.light(
        primary: Color(0xFF0F62FE),
        onPrimary: Color(0xFFFFFFFF),
        primaryContainer: Color(0xFFEDF5FF),
        secondary: Color(0xFF525252),
        onSecondary: Color(0xFFFFFFFF),
        surface: Color(0xFFFFFFFF),
        onSurface: Color(0xFF161616),
        error: Color(0xFFDA1E28),
        onError: Color(0xFFFFFFFF),
      ),
      scaffoldBackgroundColor: const Color(0xFFFFFFFF),
      appBarTheme: const AppBarTheme(
        backgroundColor: Color(0xFFFFFFFF),
        foregroundColor: Color(0xFF161616),
        elevation: 0,
        scrolledUnderElevation: 0.5,
      ),
      cardTheme: CardThemeData(
        color: const Color(0xFFFFFFFF),
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
          side: const BorderSide(color: Color(0xFFE0E0E0), width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF0F62FE),
          foregroundColor: const Color(0xFFFFFFFF),
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(0),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        ),
      ),
      inputDecorationTheme: const InputDecorationTheme(
        filled: true,
        fillColor: Color(0xFFF4F4F4),
        border: UnderlineInputBorder(
          borderSide: BorderSide(color: Color(0xFFE0E0E0), width: 1),
        ),
        enabledBorder: UnderlineInputBorder(
          borderSide: BorderSide(color: Color(0xFFE0E0E0), width: 1),
        ),
        focusedBorder: UnderlineInputBorder(
          borderSide: BorderSide(color: Color(0xFF0F62FE), width: 2),
        ),
        errorBorder: UnderlineInputBorder(
          borderSide: BorderSide(color: Color(0xFFDA1E28), width: 2),
        ),
        contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      ),
      dividerTheme: const DividerThemeData(
        color: Color(0xFFE0E0E0),
        thickness: 1,
        space: 1,
      ),
    );
  }
}
