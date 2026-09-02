import 'package:flutter/foundation.dart';

/// Base URL configuration for the ROOMMET Flask backend.
class AppConfig {
  /// Default domain fallback: local Flask server in debug mode, or Railway in release.
  static const String _defaultDomain = kDebugMode
      ? 'http://127.0.0.1:5000'
      : 'https://hostel-management-sys.up.railway.app';

  /// Root domain — can be overridden via `--dart-define=BASE_DOMAIN=...`
  static const String baseDomain = String.fromEnvironment(
    'BASE_DOMAIN',
    defaultValue: _defaultDomain,
  );

  /// Full REST API base URL used by Dio for all mobile API requests.
  static const String baseUrl = '$baseDomain/api/mobile';

  static const Duration connectTimeout = Duration(seconds: 20);
  static const Duration receiveTimeout = Duration(seconds: 40);
  static const String jwtStorageKey = 'roommet_jwt_token';
  static const String userRoleKey = 'roommet_user_role';

  /// Google OAuth 2.0 Client ID for Web / Mobile SSO
  static const String googleClientId = String.fromEnvironment(
    'GOOGLE_CLIENT_ID',
    defaultValue: '674556453436-i7d4j7srnc25oe81tvsfeccgtb6sl247.apps.googleusercontent.com',
  );

  /// Build a full URL for any relative path returned by the server
  /// (e.g. photo_url = "/static/medicines/img.jpg").
  static String fullAssetUrl(String? relativePath) {
    if (relativePath == null || relativePath.isEmpty) return '';
    if (relativePath.startsWith('http')) return relativePath;
    return '$baseDomain$relativePath';
  }

  /// Build a full URL for a secure receipt path.
  /// The receipt endpoint is served by the Flask web layer, not the mobile API.
  static String receiptUrl(String? path) {
    if (path == null || path.isEmpty) return '';
    if (path.startsWith('http')) return path;
    return '$baseDomain$path';
  }
}
