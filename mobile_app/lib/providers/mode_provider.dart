import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Modes the application can operate in.
enum AppMode { pharma, research }

/// ChangeNotifier managing the current application mode.
///
/// Supports switching between [AppMode.pharma] (sales assistant) and
/// [AppMode.research] (research assistant), and records switch history.
class ModeProvider extends ChangeNotifier {
  static const _modeKey = 'app_mode';
  static const _historyKey = 'mode_switch_history';

  AppMode _currentMode = AppMode.pharma;
  List<Map<String, dynamic>> _history = [];

  AppMode get currentMode => _currentMode;
  List<Map<String, dynamic>> get history => List.unmodifiable(_history);
  bool get isPharmaMode => _currentMode == AppMode.pharma;
  bool get isResearchMode => _currentMode == AppMode.research;

  /// Load persisted mode from SharedPreferences.
  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    final modeStr = prefs.getString(_modeKey);
    if (modeStr == 'research') {
      _currentMode = AppMode.research;
    }
    final historyJson = prefs.getString(_historyKey);
    if (historyJson != null) {
      try {
        final list = historyJson.split('||').map((e) {
          final parts = e.split('|');
          return <String, dynamic>{
            'mode': parts[0],
            'time': parts[1],
          };
        }).toList();
        _history = list;
      } catch (_) {
        _history = [];
      }
    }
    notifyListeners();
  }

  /// Switch to [mode] and record the switch in history.
  Future<void> switchMode(AppMode mode) async {
    if (mode == _currentMode) return;

    _currentMode = mode;
    _history.add({
      'mode': mode.name,
      'time': DateTime.now().toIso8601String(),
    });

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_modeKey, mode.name);

    // Keep last 50 entries.
    if (_history.length > 50) {
      _history = _history.sublist(_history.length - 50);
    }
    await prefs.setString(
      _historyKey,
      _history.map((e) => '${e['mode']}|${e['time']}').join('||'),
    );

    notifyListeners();
  }

  /// Toggle between pharma and research modes.
  Future<void> toggleMode() async {
    final next =
        _currentMode == AppMode.pharma ? AppMode.research : AppMode.pharma;
    await switchMode(next);
  }
}
