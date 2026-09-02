import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:roommet_flutter/core/config/app_config.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/storage/token_storage.dart';
import 'package:google_sign_in/google_sign_in.dart';

// ── Auth State ────────────────────────────────────────────────
enum AuthStatus { unknown, authenticated, unauthenticated }

class AuthState {
  final AuthStatus status;
  final String? role;
  final String? email;
  final bool otpRequired;
  final String? error;
  final bool isLoading;

  const AuthState({
    this.status = AuthStatus.unknown,
    this.role,
    this.email,
    this.otpRequired = false,
    this.error,
    this.isLoading = false,
  });

  AuthState copyWith({
    AuthStatus? status,
    String? role,
    String? email,
    bool? otpRequired,
    String? error,
    bool? isLoading,
  }) => AuthState(
    status: status ?? this.status,
    role: role ?? this.role,
    email: email ?? this.email,
    otpRequired: otpRequired ?? this.otpRequired,
    error: error,
    isLoading: isLoading ?? this.isLoading,
  );
}

// ── Auth Notifier ─────────────────────────────────────────────
class AuthNotifier extends StateNotifier<AuthState> {
  final ApiService _api;
  AuthNotifier(this._api) : super(const AuthState()) {
    _checkAuth();
  }

  /// Safely extract an error message from a DioException response body.
  /// Handles: Map<String,dynamic> with 'error' key, plain String, or null.
  String _extractError(DioException e, String fallback) {
    final data = e.response?.data;
    if (data == null) return fallback;
    if (data is Map) return (data['error'] ?? data['message'] ?? fallback).toString();
    if (data is String && data.isNotEmpty) return data;
    return fallback;
  }

  Future<void> _checkAuth() async {
    final isAuth = await TokenStorage.isAuthenticated();
    if (isAuth) {
      final role = await TokenStorage.getRole();
      state = AuthState(status: AuthStatus.authenticated, role: role);
    } else {
      state = const AuthState(status: AuthStatus.unauthenticated);
    }
  }

  Future<void> login(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final data = await _api.login(email, password);
      if (data['otp_required'] == true) {
        state = state.copyWith(
          isLoading: false,
          otpRequired: true,
          email: data['email'],
          status: AuthStatus.unauthenticated,
        );
        return;
      }
      final token = data['access_token'] as String;
      final role  = data['role'] as String;
      await TokenStorage.saveToken(token, role);
      state = AuthState(status: AuthStatus.authenticated, role: role);
    } on DioException catch (e) {
      final msg = _extractError(e, 'Login failed. Check your connection.');
      state = state.copyWith(isLoading: false, error: msg);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'Unexpected error: $e');
    }
  }

  Future<void> verifyOtp(String email, String otp) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final data = await _api.verifyOtp(email, otp);
      final token = data['access_token'] as String;
      final role  = data['role'] as String;
      await TokenStorage.saveToken(token, role);
      state = AuthState(status: AuthStatus.authenticated, role: role);
    } on DioException catch (e) {
      final msg = _extractError(e, 'OTP verification failed.');
      state = state.copyWith(isLoading: false, error: msg);
    }
  }

  Future<void> signInWithGoogle() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final googleSignIn = GoogleSignIn(
        clientId: AppConfig.googleClientId,
        serverClientId: AppConfig.googleClientId,
        scopes: ['email', 'profile', 'openid'],
      );
      final account = await googleSignIn.signIn();
      if (account == null) {
        state = state.copyWith(isLoading: false);
        return;
      }
      final authDetails = await account.authentication;
      final idToken = authDetails.idToken;
      final accessToken = authDetails.accessToken;
      if (idToken == null && accessToken == null) {
        state = state.copyWith(isLoading: false, error: 'Failed to retrieve Google Auth credentials.');
        return;
      }
      final data = await _api.loginWithGoogle(idToken: idToken, accessToken: accessToken);
      final token = data['access_token'] as String;
      final role  = data['role'] as String;
      await TokenStorage.saveToken(token, role);
      state = AuthState(status: AuthStatus.authenticated, role: role, email: account.email);
    } on DioException catch (e) {
      final msg = e.response?.data?['error'] ?? 'Google verification failed on server.';
      state = state.copyWith(isLoading: false, error: msg);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'Google sign-in error: $e');
    }
  }

  Future<void> logout() async {
    await TokenStorage.clear();
    state = const AuthState(status: AuthStatus.unauthenticated);
  }
}

// ── Providers ─────────────────────────────────────────────────
final apiServiceProvider = Provider<ApiService>((ref) => ApiService());

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref.read(apiServiceProvider));
});
