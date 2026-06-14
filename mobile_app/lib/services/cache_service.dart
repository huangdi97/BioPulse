import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:biopulse_app/services/database_service.dart';

class CacheService {
  final DatabaseService _db;

  CacheService(this._db);

  Future<void> cacheInsights(String userId, String insightsJson, {String pageId = 'default'}) async {
    try {
      await _db.db.delete(
        'agent_insights_cache',
        where: 'user_id = ? AND page_id = ?',
        whereArgs: [userId, pageId],
      );
      await _db.db.insert('agent_insights_cache', {
        'user_id': userId,
        'page_id': pageId,
        'insights_json': insightsJson,
      });
    } catch (e) {
      debugPrint('CacheService.cacheInsights error: $e');
    }
  }

  Future<String?> getCachedInsights(String userId, {String pageId = 'default'}) async {
    try {
      final rows = await _db.db.query(
        'agent_insights_cache',
        where: 'user_id = ? AND page_id = ? AND cached_at >= datetime(\'now\', \'-7 days\')',
        whereArgs: [userId, pageId],
        orderBy: 'cached_at DESC',
        limit: 1,
      );
      if (rows.isEmpty) return null;
      return rows.first['insights_json'] as String?;
    } catch (e) {
      debugPrint('CacheService.getCachedInsights error: $e');
      return null;
    }
  }

  Future<void> clearExpiredCache() async {
    try {
      await _db.db.delete(
        'agent_insights_cache',
        where: "cached_at < datetime('now', '-7 days')",
      );
    } catch (e) {
      debugPrint('CacheService.clearExpiredCache error: $e');
    }
  }
}
