import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // ── Palette ────────────────────────────────────────────────────
  static const Color bgDeep    = Color(0xFF0E0B1F);   // near-black indigo
  static const Color bgCard    = Color(0xFF1A1535);   // deep violet card
  static const Color bgSurface = Color(0xFF231D42);   // slightly lighter surface
  static const Color bgSecondary = bgSurface;
  static const Color accent    = Color(0xFF7C3AED);   // vibrant violet
  static const Color primary   = accent;
  static const Color accentGlow= Color(0xFFAB6DF0);   // lighter accent for glow
  static const Color success   = Color(0xFF22C55E);   // green
  static const Color warning   = Color(0xFFF59E0B);   // amber
  static const Color danger    = Color(0xFFEF4444);   // red
  static const Color info      = Color(0xFF3B82F6);   // blue
  static const Color textPrimary   = Color(0xFFE2DEFF);
  static const Color textSecondary = Color(0xFF9B89CC);
  static const Color textMuted     = Color(0xFF5C4E84);
  static const Color divider       = Color(0xFF2D2456);
  static const Color glass         = Color(0x1AFFFFFF); // 10% white
  static const Color glassBorder   = Color(0x1AFFFFFF);

  // ── Gradients ──────────────────────────────────────────────────
  static const LinearGradient bgGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFF0E0B1F), Color(0xFF1A0D38), Color(0xFF0E0B1F)],
  );

  static const LinearGradient accentGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFF7C3AED), Color(0xFF5B21B6)],
  );

  static const LinearGradient successGradient = LinearGradient(
    colors: [Color(0xFF22C55E), Color(0xFF16A34A)],
  );

  static const LinearGradient dangerGradient = LinearGradient(
    colors: [Color(0xFFEF4444), Color(0xFFDC2626)],
  );

  static const LinearGradient warningGradient = LinearGradient(
    colors: [Color(0xFFF59E0B), Color(0xFFD97706)],
  );

  // ── Card Decoration ────────────────────────────────────────────
  static BoxDecoration get glassCard => BoxDecoration(
    color: glass,
    borderRadius: BorderRadius.circular(20),
    border: Border.all(color: Colors.white.withOpacity(0.08)),
    boxShadow: [
      BoxShadow(
        color: Colors.black.withOpacity(0.3),
        blurRadius: 30,
        offset: const Offset(0, 8),
      ),
    ],
  );

  static BoxDecoration get accentCard => BoxDecoration(
    gradient: accentGradient,
    borderRadius: BorderRadius.circular(20),
    boxShadow: [
      BoxShadow(
        color: accent.withOpacity(0.4),
        blurRadius: 20,
        offset: const Offset(0, 6),
      ),
    ],
  );

  // ── Status Color helper ────────────────────────────────────────
  static Color statusColor(String status) {
    switch (status.toLowerCase()) {
      case 'active':
      case 'verified':
      case 'approved':
      case 'delivered':
        return success;
      case 'pending':
      case 'order placed':
        return warning;
      case 'rejected':
        return danger;
      case 'confirmed':
      case 'packed':
        return info;
      default:
        return textSecondary;
    }
  }

  // ── Theme Data ─────────────────────────────────────────────────
  static ThemeData get darkTheme => ThemeData(
    brightness: Brightness.dark,
    scaffoldBackgroundColor: bgDeep,
    primaryColor: accent,
    colorScheme: const ColorScheme.dark(
      primary: accent,
      secondary: accentGlow,
      surface: bgCard,
      error: danger,
    ),
    textTheme: GoogleFonts.outfitTextTheme(ThemeData.dark().textTheme).apply(
      bodyColor: textPrimary,
      displayColor: textPrimary,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: Colors.transparent,
      elevation: 0,
      centerTitle: true,
      foregroundColor: textPrimary,
      titleTextStyle: TextStyle(
        color: textPrimary,
        fontSize: 18,
        fontWeight: FontWeight.w600,
        fontFamily: 'Outfit',
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: bgSurface,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: divider),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: divider),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: accent, width: 1.5),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: danger),
      ),
      labelStyle: const TextStyle(color: textSecondary),
      hintStyle: const TextStyle(color: textMuted),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: accent,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        textStyle: const TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w600,
          fontFamily: 'Outfit',
        ),
      ),
    ),
    cardTheme: CardThemeData(
      color: bgCard,
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: bgSurface,
      labelStyle: const TextStyle(color: textSecondary, fontSize: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      side: const BorderSide(color: divider),
    ),
    dividerColor: divider,
    floatingActionButtonTheme: const FloatingActionButtonThemeData(
      backgroundColor: accent,
      foregroundColor: Colors.white,
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: bgCard,
      selectedItemColor: accent,
      unselectedItemColor: textMuted,
      type: BottomNavigationBarType.fixed,
      elevation: 0,
    ),
    snackBarTheme: SnackBarThemeData(
      backgroundColor: bgCard,
      contentTextStyle: const TextStyle(color: textPrimary, fontFamily: 'Outfit'),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      behavior: SnackBarBehavior.floating,
    ),
  );
}
