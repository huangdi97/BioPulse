import 'package:flutter/foundation.dart';
import 'package:biopulse_app/services/auth_service.dart';

/// ChangeNotifier managing authentication state across the app.
///
/// Exposes login/logout actions and observable states for
/// [isLoading], [error], and current [user].
class AuthProvider extends ChangeNotifier {
  final AuthService _authService;

  bool _isLoading = false;
  String? _error;
  Map<String, dynamic>? _user;
  bool _isLoggedIn = false;

  AuthProvider(this._authService);

  bool get isLoading => _isLoading;
  String? get error => _error;
  Map<String, dynamic>? get user => _user;
  bool get isLoggedIn => _isLoggedIn;

  /// Initialize auth state by checking for an existing token.
  Future<void> init() async {
    _isLoggedIn = await _authService.isLoggedIn();
    if (_isLoggedIn) {
      _user = await _authService.getUser();
    }
    notifyListeners();
  }

  /// Attempt login with [username] and [password].
  Future<bool> login(String username, String password, {String scope = 'visit'}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final data = await _authService.login(username, password, scope: scope);
      if (data != null) {
        _user = data;
        _isLoggedIn = true;
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _error = '用户名或密码错误';
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _error = '登录失败: $e';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  /// Switch the current user's scope (mode) via backend API.
  Future<bool> switchModeWithScope(String newScope) async {
    final success = await _authService.switchScope(newScope);
    if (success) {
      _user = await _authService.getUser();
      notifyListeners();
    }
    return success;
  }

  /// Log out and clear all user state.
  Future<bool> register(String username, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final data = await _authService.register(username, password);
      if (data != null) {
        _user = data;
        _isLoggedIn = true;
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _error = '注册失败，请重试';
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _error = '注册失败: $e';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    await _authService.logout();
    _user = null;
    _isLoggedIn = false;
    _error = null;
    notifyListeners();
  }

  /// Clear the current error message.
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
