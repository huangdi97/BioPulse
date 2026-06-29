import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:biopulse_app/services/api_client.dart';
import 'package:biopulse_app/services/dialogue_service.dart';

class _Message {
  final String text;
  final bool isUser;
  final bool isSystem;
  const _Message({required this.text, this.isUser = false, this.isSystem = false});
}

class DialoguePanel extends StatefulWidget {
  final String agentKey;
  final String agentName;
  final Map<String, dynamic> context;
  final VoidCallback onClose;

  const DialoguePanel({
    super.key,
    required this.agentKey,
    required this.agentName,
    required this.context,
    required this.onClose,
  });

  @override
  State<DialoguePanel> createState() => _DialoguePanelState();
}

class _DialoguePanelState extends State<DialoguePanel> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  final _focusNode = FocusNode();
  List<_Message> _messages = [];
  String? _sessionId;
  bool _isLoadingSession = true;
  bool _isSending = false;
  String? _errorText;
  late DialogueService _service;

  @override
  void initState() {
    super.initState();
    _service = DialogueService(context.read<ApiClient>());
    _initSession();
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  Future<void> _initSession() async {
    final summary = widget.context['summary'] as String?;
    if (summary != null && summary.isNotEmpty) {
      setState(() => _messages.add(_Message(
        text: '关于「$summary」，你可以追问为什么、反馈误报等', isSystem: true,
      )));
    }
    try {
      final result = await _service.createSession(widget.agentKey, '', widget.context);
      setState(() { _sessionId = result['session_id'] as String?; _isLoadingSession = false; });
    } catch (_) {
      setState(() { _isLoadingSession = false; _errorText = '创建对话失败，请重试'; });
    }
  }

  Future<void> _sendMessage() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _sessionId == null || _isSending) return;
    _controller.clear();
    setState(() { _messages.add(_Message(text: text, isUser: true)); _isSending = true; });
    _scrollToBottom();
    try {
      final result = await _service.sendMessage(_sessionId!, text);
      final reply = result['reply'] as String? ?? '';
      setState(() { _messages.add(_Message(text: reply)); _isSending = false; });
      _scrollToBottom();
    } catch (_) {
      setState(() { _messages.add(const _Message(text: '发送失败，请重试')); _isSending = false; });
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200), curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: SizedBox(
        height: MediaQuery.of(context).size.height * 0.7,
        child: Column(children: [
          _buildTitleBar(),
          const Divider(height: 1),
          Expanded(child: _buildMessageList()),
          _buildInputBar(),
        ]),
      ),
    );
  }

  Widget _buildTitleBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: Row(children: [
        const SizedBox(width: 8),
        Expanded(child: Text('${widget.agentName} · 对话',
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600))),
        IconButton(icon: const Icon(Icons.close), onPressed: widget.onClose),
      ]),
    );
  }

  Widget _buildMessageList() {
    if (_isLoadingSession) return const Center(child: CircularProgressIndicator());
    if (_errorText != null) {
      return Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
        Text(_errorText!, style: const TextStyle(color: Colors.red)),
        const SizedBox(height: 8),
        TextButton(onPressed: () { setState(() { _errorText = null; _isLoadingSession = true; }); _initSession(); }, child: const Text('重试')),
      ]));
    }
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      itemCount: _messages.length,
      itemBuilder: (_, i) {
        final msg = _messages[i];
        if (msg.isSystem) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Container(
              width: double.infinity, padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: BorderRadius.circular(8)),
              child: Text(msg.text, style: TextStyle(fontSize: 13, color: Colors.grey.shade700), textAlign: TextAlign.center),
            ),
          );
        }
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Row(
            mainAxisAlignment: msg.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
            children: [
              if (!msg.isUser) ...[
                CircleAvatar(radius: 14, backgroundColor: Colors.blue.shade100,
                  child: Text(widget.agentName.isNotEmpty ? widget.agentName.substring(0, 1) : 'A', style: const TextStyle(fontSize: 12))),
                const SizedBox(width: 8),
              ],
              Flexible(child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: msg.isUser ? Colors.blue : Colors.grey.shade200,
                  borderRadius: BorderRadius.only(
                    topLeft: const Radius.circular(16), topRight: const Radius.circular(16),
                    bottomLeft: msg.isUser ? const Radius.circular(16) : Radius.zero,
                    bottomRight: msg.isUser ? Radius.zero : const Radius.circular(16),
                  ),
                ),
                child: Text(msg.text, style: TextStyle(color: msg.isUser ? Colors.white : Colors.black87, fontSize: 14)),
              )),
              if (msg.isUser) const SizedBox(width: 8),
            ],
          ),
        );
      },
    );
  }

  Widget _buildInputBar() {
    return Container(
      decoration: BoxDecoration(color: Colors.white, border: Border(top: BorderSide(color: Colors.grey.shade300))),
      padding: const EdgeInsets.only(left: 12, right: 8, top: 8, bottom: 8),
      child: Row(children: [
        Expanded(child: TextField(
          controller: _controller, focusNode: _focusNode,
          textInputAction: TextInputAction.send,
          onSubmitted: (_) => _sendMessage(),
          decoration: const InputDecoration(
            hintText: '输入问题…',
            contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(20))),
            isDense: true,
          ),
        )),
        const SizedBox(width: 8),
        _isSending
            ? const SizedBox(width: 36, height: 36, child: Center(child: CircularProgressIndicator(strokeWidth: 2)))
            : IconButton(icon: const Icon(Icons.send), color: Colors.blue, onPressed: _sendMessage),
      ]),
    );
  }
}