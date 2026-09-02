import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:roommet_flutter/core/config/app_config.dart';

class TokenStorage {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
    iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
  );

  /// Save JWT token and user role securely
  static Future<void> saveToken(String token, String role) async {
    await _storage.write(key: AppConfig.jwtStorageKey, value: token);
    await _storage.write(key: AppConfig.userRoleKey, value: role);
  }

  /// Read the JWT token
  static Future<String?> getToken() async {
    return _storage.read(key: AppConfig.jwtStorageKey);
  }

  /// Read the user role
  static Future<String?> getRole() async {
    return _storage.read(key: AppConfig.userRoleKey);
  }

  /// Delete token and role (logout)
  static Future<void> clear() async {
    await _storage.delete(key: AppConfig.jwtStorageKey);
    await _storage.delete(key: AppConfig.userRoleKey);
  }

  /// Check if user is authenticated (token exists)
  static Future<bool> isAuthenticated() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }
}
