import 'package:dio/dio.dart';
import 'package:one_cloud_app/services/auth_service.dart';

/// Dio HTTP client wrapper with token refresh and response unwrapping.
class ApiClient {
  late final Dio _dio;
  final AuthService _authService;
  final String baseUrl;
  bool _isRefreshing = false;
  String? _pendingToken;

  ApiClient({
    required this.baseUrl,
    required AuthService authService,
  }) : _authService = authService {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 15),
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: _onRequest,
      onError: _onError,
    ));
  }

  void _onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final token = _authService.getTokenSync();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  Future<void> _onError(
    DioException error,
    ErrorInterceptorHandler handler,
  ) async {
    if (error.response?.statusCode != 401) {
      return handler.next(error);
    }

    if (_isRefreshing) {
      final token = _pendingToken;
      if (token != null) {
        error.requestOptions.headers['Authorization'] = 'Bearer $token';
        return handler.resolve(await _retry(error.requestOptions));
      }
      return handler.next(error);
    }

    _isRefreshing = true;
    try {
      final newToken = await _authService.refreshToken();
      _pendingToken = newToken;
      if (newToken != null) {
        await _authService.saveToken(newToken);
        error.requestOptions.headers['Authorization'] = 'Bearer $newToken';
        return handler.resolve(await _retry(error.requestOptions));
      }
    } finally {
      _isRefreshing = false;
      _pendingToken = null;
    }

    return handler.next(error);
  }

  Future<Response> _retry(RequestOptions requestOptions) async {
    return _dio.fetch(requestOptions);
  }

  ApiResponse<T> _unwrap<T>(Response<dynamic> response) {
    final body = response.data as Map<String, dynamic>?;
    if (body == null) {
      return ApiResponse<T>(
        code: -1,
        message: 'Empty response',
        data: null,
        requestId: null,
      );
    }
    return ApiResponse<T>(
      code: body['code'] as int? ?? -1,
      message: body['message'] as String? ?? '',
      data: body['data'] as T?,
      requestId: body['request_id'] as String?,
    );
  }

  Future<ApiResponse<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
  }) async {
    final response = await _dio.get(path, queryParameters: queryParameters);
    return _unwrap<T>(response);
  }

  Future<ApiResponse<T>> post<T>(
    String path, {
    dynamic data,
  }) async {
    final response = await _dio.post(path, data: data);
    return _unwrap<T>(response);
  }

  Future<ApiResponse<T>> put<T>(
    String path, {
    dynamic data,
  }) async {
    final response = await _dio.put(path, data: data);
    return _unwrap<T>(response);
  }

  Future<ApiResponse<T>> delete<T>(
    String path, {
    dynamic data,
  }) async {
    final response = await _dio.delete(path, data: data);
    return _unwrap<T>(response);
  }
}

/// Manages multiple named [ApiClient] instances for different backends.
///
/// Each backend is identified by a unique name (e.g. "main", "sync") and
/// configured with its own [baseUrl]. All clients share the same [AuthService]
/// for token management.
class MultiBackendApiClient {
  final Map<String, ApiClient> _clients = {};
  final AuthService _authService;
  final String _defaultName;

  /// Creates a [MultiBackendApiClient] with the given [backends].
  ///
  /// [backends] is a map of backend names to their base URLs.
  /// The first entry becomes the default backend unless [defaultName] is set.
  /// All backends share the provided [authService].
  MultiBackendApiClient({
    required AuthService authService,
    required Map<String, String> backends,
    String? defaultName,
  })  : _authService = authService,
      _defaultName = defaultName ?? backends.keys.first {
    for (final entry in backends.entries) {
      _clients[entry.key] = ApiClient(
        baseUrl: entry.value,
        authService: authService,
      );
    }
  }

  /// Retrieve the [ApiClient] registered under [name].
  /// Throws [ArgumentError] if no backend with that name exists.
  ApiClient getClient(String name) {
    final client = _clients[name];
    if (client == null) {
      throw ArgumentError('Unknown backend: $name. Available: ${_clients.keys.join(", ")}');
    }
    return client;
  }

  /// The default [ApiClient] (first registered backend or the one specified).
  ApiClient get defaultClient => getClient(_defaultName);

  /// Register or replace a backend with the given [name] and [baseUrl].
  void addBackend(String name, String baseUrl) {
    _clients[name] = ApiClient(
      baseUrl: baseUrl,
      authService: _authService,
    );
  }

  /// List all registered backend names.
  Iterable<String> get backendNames => _clients.keys;

  // -- Convenience delegates to the default client --

  Future<ApiResponse<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
  }) =>
      defaultClient.get<T>(path, queryParameters: queryParameters);

  Future<ApiResponse<T>> post<T>(
    String path, {
    dynamic data,
  }) =>
      defaultClient.post<T>(path, data: data);

  Future<ApiResponse<T>> put<T>(
    String path, {
    dynamic data,
  }) =>
      defaultClient.put<T>(path, data: data);

  Future<ApiResponse<T>> delete<T>(
    String path, {
    dynamic data,
  }) =>
      defaultClient.delete<T>(path, data: data);
}

/// Standard API response wrapper matching {code, message, data, request_id}.
class ApiResponse<T> {
  final int code;
  final String message;
  final T? data;
  final String? requestId;

  bool get isSuccess => code == 0;

  const ApiResponse({
    required this.code,
    required this.message,
    this.data,
    this.requestId,
  });
}
