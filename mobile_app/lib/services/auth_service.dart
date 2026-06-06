import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:one_cloud_app/services/api_client.dart';

/// Authentication service managing login, logout, and token persistence.
///
/// Stores tokens in SharedPreferences and integrates with [ApiClient]
/// for API authentication calls.
class AuthService {
  static const _tokenKey = 'auth_token';
  static const _refreshTokenKey = 'auth_refresh_token';
  static const _tokenExpiryKey = 'auth_token_expiry';
  static const _userKey = 'auth_user';

  ApiClient? _apiClient;
  SharedPreferences? _prefs;

  /// Set the API client (called after circular dependencies are resolved).
  void setApiClient(ApiClient client) {
    _apiClient = client;
  }

  ApiClient get _client {
    if (_apiClient == null) {
      throw StateError('ApiClient not set. Call setApiClient() first.');
    }
    return _apiClient!;
  }

  Future<SharedPreferences> get _preferences async {
    return _prefs ??= await SharedPreferences.getInstance();
  }

  /// Log in with [username] and [password].
  /// Returns user data on success or null on failure.
  Future<Map<String, dynamic>?> login(String username, String password, {String scope = 'visit'}) async {
    final response = await _client.post<Map<String, dynamic>>(
      '/auth/login',
      data: {'username': username, 'password': password, 'scope': scope},
    );

    if (!response.isSuccess || response.data == null) {
      return null;
    }

    final data = response.data!;
    final token = data['token'] as String?;
    final refreshToken = data['refresh_token'] as String?;
    final expiry = data['expires_in'] as int?;

    if (token != null) {
      await saveToken(token);
      if (refreshToken != null) {
        await _saveRefreshToken(refreshToken);
      }
      if (expiry != null) {
        await _saveTokenExpiry(
          DateTime.now().millisecondsSinceEpoch + expiry * 1000,
        );
      }
      await _saveUser(data);
    }

    return data;
  }

  /// Switch the current user's scope by calling /auth/switch-mode.
  /// Saves the new token on success.
  Future<bool> switchScope(String newScope) async {
    final response = await _client.post<Map<String, dynamic>>(
      '/auth/switch-mode',
      data: {'new_scope': newScope},
    );
    if (!response.isSuccess || response.data == null) return false;
    final token = response.data!['access_token'] as String?;
    if (token == null) return false;
    await saveToken(token);
    return true;
  }

  /// Log out by clearing all stored auth data.
  Future<Map<String, dynamic>?> register(String username, String password) async {
    final response = await _client.post<Map<String, dynamic>>(
      '/auth/register',
      data: {'username': username, 'password': password},
    );
    if (!response.isSuccess || response.data == null) return null;
    final data = response.data!;
    final token = data['token'] as String?;
    final refreshToken = data['refresh_token'] as String?;
    final expiry = data['expires_in'] as int?;
    if (token != null) {
      await saveToken(token);
      if (refreshToken != null) await _saveRefreshToken(refreshToken);
      if (expiry != null) await _saveTokenExpiry(DateTime.now().millisecondsSinceEpoch + expiry * 1000);
      await _saveUser(data);
    }
    return data;
  }

  Future<void> logout() async {
    final prefs = await _preferences;
    await prefs.remove(_tokenKey);
    await prefs.remove(_refreshTokenKey);
    await prefs.remove(_tokenExpiryKey);
    await prefs.remove(_userKey);
  }

  /// Save [token] to local storage.
  Future<void> saveToken(String token) async {
    final prefs = await _preferences;
    await prefs.setString(_tokenKey, token);
  }

  /// Get the stored access token.
  Future<String?> getToken() async {
    final prefs = await _preferences;
    return prefs.getString(_tokenKey);
  }

  /// Synchronously get the stored token (for interceptors).
  String? getTokenSync() {
    return _prefs?.getString(_tokenKey);
  }

  /// Check whether a valid (non-expired) token exists.
  Future<bool> isLoggedIn() async {
    final prefs = await _preferences;
    final token = prefs.getString(_tokenKey);
    if (token == null) return false;

    final expiry = prefs.getInt(_tokenExpiryKey);
    if (expiry == null) return true;

    return DateTime.now().millisecondsSinceEpoch < expiry;
  }

  /// Attempt to refresh the access token using the stored refresh token.
  Future<String?> refreshToken() async {
    final prefs = await _preferences;
    final refreshToken = prefs.getString(_refreshTokenKey);
    if (refreshToken == null) return null;

    try {
      final response = await _client.post<Map<String, dynamic>>(
        '/auth/refresh',
        data: {'refresh_token': refreshToken},
      );

      if (!response.isSuccess || response.data == null) return null;

      final newToken = response.data!['token'] as String?;
      return newToken;
    } catch (_) {
      return null;
    }
  }

  /// Get stored user info.
  Future<Map<String, dynamic>?> getUser() async {
    final prefs = await _preferences;
    final json = prefs.getString(_userKey);
    if (json == null) return null;
    return jsonDecode(json) as Map<String, dynamic>;
  }

  Future<void> _saveRefreshToken(String token) async {
    final prefs = await _preferences;
    await prefs.setString(_refreshTokenKey, token);
  }

  Future<void> _saveTokenExpiry(int expiry) async {
    final prefs = await _preferences;
    await prefs.setInt(_tokenExpiryKey, expiry);
  }

  Future<void> _saveUser(Map<String, dynamic> user) async {
    final prefs = await _preferences;
    await prefs.setString(_userKey, jsonEncode(user));
  }
}
