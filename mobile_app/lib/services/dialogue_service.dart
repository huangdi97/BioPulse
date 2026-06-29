import 'package:biopulse_app/services/api_client.dart';

class DialogueService {
  final ApiClient _api;

  DialogueService(this._api);

  Future<Map<String, dynamic>> createSession(
    String agentKey,
    String userId,
    Map<String, dynamic> context,
  ) async {
    final response = await _api.post<Map>(
      '/api/v1/dialogue/session',
      data: {
        'agent_key': agentKey,
        'user_id': userId,
        'context': context,
      },
    );
    return response.data!;
  }

  Future<Map<String, dynamic>> sendMessage(
    String sessionId,
    String message,
  ) async {
    final response = await _api.post<Map>(
      '/api/v1/dialogue/send',
      data: {
        'session_id': sessionId,
        'message': message,
      },
    );
    return response.data!;
  }

  Future<Map<String, dynamic>> submitFeedback(
    String type,
    String targetId,
    String content,
    String sessionId,
  ) async {
    final response = await _api.post<Map>(
      '/api/v1/dialogue/feedback',
      data: {
        'type': type,
        'target_id': targetId,
        'content': content,
        'session_id': sessionId,
      },
    );
    return response.data!;
  }
}