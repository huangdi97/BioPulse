import 'dart:async';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:one_cloud_app/models/hcp.dart';
import 'package:one_cloud_app/models/visit.dart';
import 'package:one_cloud_app/models/surgery.dart';
import 'package:one_cloud_app/constants/app_constants.dart';
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
    final serverUrl = prefs.getString(_serverUrlKey) ?? AppConstants.syncUrl;
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

  Future<int> pullHcps(String baseUrl) async {
    try {
      final response = await _dio
          .get('$baseUrl/hcp')
          .timeout(const Duration(seconds: 10));
      final list = _extractList(response.data);
      int count = 0;
      for (final item in list) {
        final hcp = HCP.fromMap(item as Map<String, dynamic>);
        final existing = await _db.db.query(
          'hcps',
          where: 'name = ? AND hospital = ?',
          whereArgs: [hcp.name, hcp.hospital],
        );
        final map = hcp.toMap();
        map.remove('id');
        if (existing.isNotEmpty) {
          await _db.db.update(
            'hcps',
            map,
            where: 'id = ?',
            whereArgs: [existing.first['id']],
          );
        } else {
          await _db.db.insert('hcps', map);
        }
        count++;
      }
      return count;
    } catch (_) {
      return 0;
    }
  }

  Future<int> pullVisits(String baseUrl) async {
    try {
      final response = await _dio
          .get('$baseUrl/visit')
          .timeout(const Duration(seconds: 10));
      final list = _extractList(response.data);
      int count = 0;
      for (final item in list) {
        final visit = Visit.fromMap(item as Map<String, dynamic>);
        final existing = await _db.db.query(
          'visits',
          where: 'hcp_name = ? AND visit_date = ?',
          whereArgs: [visit.hcpName, visit.visitDate],
        );
        final map = visit.toMap();
        map.remove('id');
        if (existing.isNotEmpty) {
          await _db.db.update(
            'visits',
            map,
            where: 'id = ?',
            whereArgs: [existing.first['id']],
          );
        } else {
          await _db.db.insert('visits', map);
        }
        count++;
      }
      return count;
    } catch (_) {
      return 0;
    }
  }

  Future<int> pullSurgeries(String baseUrl) async {
    try {
      final response = await _dio
          .get('$baseUrl/surgery')
          .timeout(const Duration(seconds: 10));
      final list = _extractList(response.data);
      int count = 0;
      for (final item in list) {
        final surgery = Surgery.fromMap(item as Map<String, dynamic>);
        final existing = await _db.db.query(
          'surgeries',
          where: 'patient_name = ? AND scheduled_date = ?',
          whereArgs: [surgery.patientName, surgery.scheduledDate],
        );
        final map = surgery.toMap();
        map.remove('id');
        if (existing.isNotEmpty) {
          await _db.db.update(
            'surgeries',
            map,
            where: 'id = ?',
            whereArgs: [existing.first['id']],
          );
        } else {
          await _db.db.insert('surgeries', map);
        }
        count++;
      }
      return count;
    } catch (_) {
      return 0;
    }
  }

  Future<Map<String, int>> pullAll(Map<String, String> backendUrls) async {
    final hcpUrl =
        backendUrls['assistant'] ?? backendUrls['sales_assistant'];
    final visitUrl =
        backendUrls['assistant'] ?? backendUrls['sales_assistant'];
    final surgeryUrl =
        backendUrls['assistant'] ?? backendUrls['sales_assistant'];

    final hcpCount = hcpUrl != null ? await pullHcps(hcpUrl) : 0;
    final visitCount = visitUrl != null ? await pullVisits(visitUrl) : 0;
    final surgeryCount =
        surgeryUrl != null ? await pullSurgeries(surgeryUrl) : 0;

    return {
      'hcp': hcpCount,
      'visits': visitCount,
      'surgeries': surgeryCount,
    };
  }

  List<dynamic> _extractList(dynamic data) {
    if (data is List) return data;
    if (data is Map && data['data'] is List) return data['data'] as List<dynamic>;
    if (data is Map && data['data'] is Map) {
      final inner = data['data'] as Map;
      if (inner['records'] is List) return inner['records'] as List<dynamic>;
      if (inner['items'] is List) return inner['items'] as List<dynamic>;
      if (inner['list'] is List) return inner['list'] as List<dynamic>;
    }
    return [];
  }
}
