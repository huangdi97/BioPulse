import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'package:biopulse_app/models/visit.dart';
import 'package:biopulse_app/models/surgery.dart';
import 'package:biopulse_app/models/hcp.dart';
import 'package:biopulse_app/models/pi_profile.dart';
import 'package:biopulse_app/models/quotation.dart';

/// Local SQLite database service for offline-first data storage.
///
/// Manages tables for visits, surgeries, patients, and a sync queue
/// for pending records that need to be synced with the server.
class DatabaseService {
  static Database? _database;
  static const String _dbName = 'biopulse_app.db';
  static const int _dbVersion = 4;

  /// Initialize the database and create tables if they do not exist.
  Future<Database> initDatabase() async {
    if (_database != null) return _database!;

    final dbPath = await getDatabasesPath();
    final path = join(dbPath, _dbName);

    _database = await openDatabase(
      path,
      version: _dbVersion,
      onCreate: _onCreate,
      onUpgrade: _onUpgrade,
    );

    return _database!;
  }

  Future<void> _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hcp_name TEXT NOT NULL,
        hospital TEXT NOT NULL,
        department TEXT,
        visit_date TEXT NOT NULL,
        visit_type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        notes TEXT,
        compliance_status TEXT,
        products TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
      )
    ''');

    await db.execute('''
      CREATE TABLE surgeries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT NOT NULL,
        hospital TEXT NOT NULL,
        surgery_type TEXT NOT NULL,
        scheduled_date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'scheduled',
        prep_checklist TEXT,
        intra_op_notes TEXT,
        post_op_report TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
      )
    ''');

    await db.execute('''
      CREATE TABLE patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        gender TEXT,
        age INTEGER,
        hospital TEXT,
        diagnosis TEXT,
        phone TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
      )
    ''');

    await db.execute('''
      CREATE TABLE hcps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        hospital TEXT NOT NULL,
        department TEXT,
        title TEXT,
        phone TEXT,
        email TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        tags TEXT,
        last_visit_date TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
      )
    ''');

    await db.execute('''
      CREATE TABLE sync_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_name TEXT NOT NULL,
        record_id INTEGER NOT NULL,
        operation TEXT NOT NULL CHECK(operation IN ('create','update','delete')),
        payload TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
      )
    ''');
  }

  Future<void> _onUpgrade(Database db, int oldVersion, int newVersion) async {
    if (oldVersion < 2) {
      await db.execute('''
        CREATE TABLE IF NOT EXISTS hcps (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          hospital TEXT NOT NULL,
          department TEXT,
          title TEXT,
          phone TEXT,
          email TEXT,
          is_active INTEGER NOT NULL DEFAULT 1,
          tags TEXT,
          last_visit_date TEXT,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
      ''');
    }
    if (oldVersion < 3) {
      try {
        await db.execute('ALTER TABLE sync_queue ADD COLUMN action TEXT');
      } catch (_) {}
      try {
        await db.execute('ALTER TABLE sync_queue ADD COLUMN server_url TEXT');
      } catch (_) {}
      await db.execute('''
        CREATE TABLE IF NOT EXISTS pi_profiles (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          institution TEXT,
          papers_count INTEGER DEFAULT 0,
          h_index INTEGER DEFAULT 0,
          research_areas TEXT,
          active_years TEXT,
          bio TEXT,
          photo_url TEXT,
          created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
      ''');
      await db.execute('''
        CREATE TABLE IF NOT EXISTS quotations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          pi_name TEXT NOT NULL,
          products TEXT,
          total_amount REAL DEFAULT 0,
          status TEXT NOT NULL DEFAULT 'draft',
          created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
      ''');
    if (oldVersion < 4) {
      await db.execute('''
        CREATE TABLE IF NOT EXISTS agent_insights_cache (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id TEXT NOT NULL,
          page_id TEXT NOT NULL DEFAULT 'default',
          insights_json TEXT NOT NULL,
          cached_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
      ''');
    }
    }
  }

  Database get db {
    if (_database == null) {
      throw StateError('Database not initialized. Call initDatabase() first.');
    }
    return _database!;
  }

  // ---------------------------------------------------------------------------
  // Visits CRUD
  // ---------------------------------------------------------------------------

  Future<int> insertVisit(Visit visit) async {
    return db.insert('visits', visit.toMap());
  }

  Future<List<Visit>> getVisits({String? statusFilter}) async {
    String? where;
    List<dynamic>? whereArgs;
    if (statusFilter != null) {
      where = 'status = ?';
      whereArgs = [statusFilter];
    }
    final maps = await db.query(
      'visits',
      where: where,
      whereArgs: whereArgs,
      orderBy: 'visit_date DESC',
    );
    return maps.map((m) => Visit.fromMap(m)).toList();
  }

  Future<Visit?> getVisit(int id) async {
    final maps = await db.query('visits', where: 'id = ?', whereArgs: [id]);
    if (maps.isEmpty) return null;
    return Visit.fromMap(maps.first);
  }

  Future<int> updateVisit(Visit visit) async {
    return db.update(
      'visits',
      visit.toMap(),
      where: 'id = ?',
      whereArgs: [visit.id],
    );
  }

  Future<int> deleteVisit(int id) async {
    return db.delete('visits', where: 'id = ?', whereArgs: [id]);
  }

  // ---------------------------------------------------------------------------
  // Surgeries CRUD
  // ---------------------------------------------------------------------------

  Future<int> insertSurgery(Surgery surgery) async {
    return db.insert('surgeries', surgery.toMap());
  }

  Future<List<Surgery>> getSurgeries({String? statusFilter}) async {
    String? where;
    List<dynamic>? whereArgs;
    if (statusFilter != null) {
      where = 'status = ?';
      whereArgs = [statusFilter];
    }
    final maps = await db.query(
      'surgeries',
      where: where,
      whereArgs: whereArgs,
      orderBy: 'scheduled_date DESC',
    );
    return maps.map((m) => Surgery.fromMap(m)).toList();
  }

  Future<Surgery?> getSurgery(int id) async {
    final maps = await db.query('surgeries', where: 'id = ?', whereArgs: [id]);
    if (maps.isEmpty) return null;
    return Surgery.fromMap(maps.first);
  }

  Future<int> updateSurgery(Surgery surgery) async {
    return db.update(
      'surgeries',
      surgery.toMap(),
      where: 'id = ?',
      whereArgs: [surgery.id],
    );
  }

  Future<int> deleteSurgery(int id) async {
    return db.delete('surgeries', where: 'id = ?', whereArgs: [id]);
  }

  // ---------------------------------------------------------------------------
  // HCPs CRUD
  // ---------------------------------------------------------------------------

  Future<int> insertHCP(HCP hcp) async {
    return db.insert('hcps', hcp.toMap());
  }

  Future<List<HCP>> getHCPs() async {
    final maps = await db.query('hcps', orderBy: 'name ASC');
    return maps.map((m) => HCP.fromMap(m)).toList();
  }

  Future<HCP?> getHCP(int id) async {
    final maps = await db.query('hcps', where: 'id = ?', whereArgs: [id]);
    if (maps.isEmpty) return null;
    return HCP.fromMap(maps.first);
  }

  Future<List<HCP>> searchHCPs(String query) async {
    final maps = await db.query(
      'hcps',
      where: 'name LIKE ? OR hospital LIKE ?',
      whereArgs: ['%$query%', '%$query%'],
      orderBy: 'name ASC',
    );
    return maps.map((m) => HCP.fromMap(m)).toList();
  }

  Future<List<Visit>> getVisitsByHCP(String hcpName) async {
    final maps = await db.query(
      'visits',
      where: 'hcp_name = ?',
      whereArgs: [hcpName],
      orderBy: 'visit_date DESC',
    );
    return maps.map((m) => Visit.fromMap(m)).toList();
  }

  Future<int> updateHCP(HCP hcp) async {
    return db.update(
      'hcps',
      hcp.toMap(),
      where: 'id = ?',
      whereArgs: [hcp.id],
    );
  }

  Future<int> updateHCPLastVisit(int id, String date) async {
    return db.update(
      'hcps',
      {'last_visit_date': date},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<int> deleteHCP(int id) async {
    return db.delete('hcps', where: 'id = ?', whereArgs: [id]);
  }

  // ---------------------------------------------------------------------------
  // Sync Queue
  // ---------------------------------------------------------------------------

  /// Add a record to the sync queue for later upload.
  Future<int> addToSyncQueue({
    required String tableName,
    required int recordId,
    required String action,
    String? payload,
    String? serverUrl,
  }) async {
    return db.insert('sync_queue', {
      'table_name': tableName,
      'record_id': recordId,
      'action': action,
      'payload': payload,
      'server_url': serverUrl,
    });
  }

  /// Get all pending sync records.
  Future<List<Map<String, dynamic>>> getPendingSyncRecords() async {
    return db.query('sync_queue', where: 'status = ?', whereArgs: ['pending']);
  }

  /// Get the count of pending sync records.
  Future<int> getPendingSyncCount() async {
    final result = await db.rawQuery(
      'SELECT COUNT(*) as cnt FROM sync_queue WHERE status = ?',
      ['pending'],
    );
    return (result.first['cnt'] as int?) ?? 0;
  }

  /// Mark a sync record as completed.
  Future<void> markSyncCompleted(int syncId) async {
    await db.update(
      'sync_queue',
      {'status': 'completed'},
      where: 'id = ?',
      whereArgs: [syncId],
    );
  }

  // ---------------------------------------------------------------------------
  // PI Profiles CRUD
  // ---------------------------------------------------------------------------

  Future<int> insertPIProfile(PIProfile profile) async {
    return db.insert('pi_profiles', profile.toMap());
  }

  Future<List<PIProfile>> getPIProfiles() async {
    final maps = await db.query('pi_profiles', orderBy: 'name ASC');
    return maps.map((m) => PIProfile.fromMap(m)).toList();
  }

  Future<PIProfile?> getPIProfile(int id) async {
    final maps = await db.query('pi_profiles', where: 'id = ?', whereArgs: [id]);
    if (maps.isEmpty) return null;
    return PIProfile.fromMap(maps.first);
  }

  Future<List<PIProfile>> searchPIProfiles(String query) async {
    final maps = await db.query(
      'pi_profiles',
      where: 'name LIKE ? OR institution LIKE ?',
      whereArgs: ['%$query%', '%$query%'],
      orderBy: 'name ASC',
    );
    return maps.map((m) => PIProfile.fromMap(m)).toList();
  }

  // ---------------------------------------------------------------------------
  // Quotations CRUD
  // ---------------------------------------------------------------------------

  Future<int> insertQuotation(Quotation quotation) async {
    return db.insert('quotations', quotation.toMap());
  }

  Future<List<Quotation>> getQuotations() async {
    final maps = await db.query('quotations', orderBy: 'created_at DESC');
    return maps.map((m) => Quotation.fromMap(m)).toList();
  }

  Future<Quotation?> getQuotation(int id) async {
    final maps = await db.query('quotations', where: 'id = ?', whereArgs: [id]);
    if (maps.isEmpty) return null;
    return Quotation.fromMap(maps.first);
  }

  Future<int> updateQuotation(Quotation quotation) async {
    return db.update(
      'quotations',
      quotation.toMap(),
      where: 'id = ?',
      whereArgs: [quotation.id],
    );
  }

  Future<int> deleteQuotation(int id) async {
    return db.delete('quotations', where: 'id = ?', whereArgs: [id]);
  }

  /// Close the database connection.
  Future<void> close() async {
    await _database?.close();
    _database = null;
  }
}
