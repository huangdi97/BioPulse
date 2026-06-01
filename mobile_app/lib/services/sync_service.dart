import 'dart:async';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:one_cloud_app/services/database_service.dart';

class SyncService {
  final DatabaseService _db;
  final Dio _dio;
  Timer? _timer;
  bool _isSyncing = false;

  static const _serverUrlKey = 'server_base_url';

  SyncService(this._db, this._dio);

  Future<int> addToSyncQueue(String table, int recordId, String action) async {
    final prefs = await SharedPreferences.getInstance();
    final serverUrl = prefs.getString(_serverUrlKey) ?? 'https://api.example.com';
    return _db.addToSyncQueue(
      tableName: table,
      recordId: recordId,
      action: action,
      serverUrl: serverUrl,
    );
  }

  Future<int> getPendingCount() async {
    return _db.getPendingSyncCount();
  }

  Future<void> syncPending() async {
    if (_isSyncing) return;
    _isSyncing = true;
    try {
      final records = await _db.getPendingSyncRecords();
      for (final record in records) {
        try {
          final url = record['server_url'] as String? ?? 'https://api.example.com';
          final action = record['action'] as String? ?? 'create';
          final tableName = record['table_name'] as String;
          final recordId = record['record_id'] as int;

          await _dio.post(
            '$url/sync/$tableName',
            data: {
              'action': action,
              'record_id': recordId,
              'payload': record['payload'],
            },
          );
          await _db.markSyncCompleted(record['id'] as int);
        } catch (_) {
          continue;
        }
      }
    } finally {
      _isSyncing = false;
    }
  }

  void startAutoSync() {
    _timer = Timer.periodic(
      const Duration(minutes: 5),
      (_) => syncPending(),
    );
  }

  void stopAutoSync() {
    _timer?.cancel();
    _timer = null;
  }

  void dispose() {
    stopAutoSync();
    _dio.close();
  }
}
