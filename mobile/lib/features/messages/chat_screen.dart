/// Chat screen — message thread with bubbles, read receipts, real-time via WebSocket.
///
/// Reference: Phase 12B — Chat screen
/// Listens to WS events for incoming messages in this conversation.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/data/api/ws_client.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/domain/entities/conversation.dart';
import 'messages_provider.dart';

class ChatScreen extends ConsumerStatefulWidget {
  final String conversationId;

  const ChatScreen({super.key, required this.conversationId});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  VoidCallback? _wsUnsub;

  @override
  void initState() {
    super.initState();
    // Subscribe to WS for real-time messages
    final ws = ref.read(wsClientProvider);
    _wsUnsub = ws.subscribe((event) {
      if (event.type == WsEventType.notificationCreated) {
        final eventType = event.data['event_type'] as String?;
        final convId = event.data['conversation_id'] as String?;
        if (eventType == 'message_created' && convId == widget.conversationId) {
          // Reload messages
          ref.read(chatProvider(widget.conversationId).notifier).load();
        }
      }
    });
  }

  @override
  void dispose() {
    _wsUnsub?.call();
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(chatProvider(widget.conversationId));
    final t = AppLocalizations.of(ref);
    final userId = ref.watch(authProvider).user?.id ?? '';
    final theme = Theme.of(context);

    // Scroll to bottom on new messages
    if (state.messages.isNotEmpty) {
      _scrollToBottom();
    }

    return Scaffold(
      appBar: AppBar(title: Text(t.t('messages.chat'))),
      body: Column(
        children: [
          // Messages
          Expanded(
            child: state.isLoading
                ? const Center(child: CircularProgressIndicator())
                : state.error != null && state.messages.isEmpty
                    ? Center(child: Text(state.error!))
                    : state.messages.isEmpty
                        ? Center(
                            child: Text(t.t('messages.noMessages'),
                                style: theme.textTheme.bodyMedium?.copyWith(
                                    color: theme.colorScheme.onSurfaceVariant)))
                        : ListView.builder(
                            controller: _scrollController,
                            padding: const EdgeInsets.symmetric(
                                horizontal: 12, vertical: 8),
                            itemCount: state.messages.length,
                            itemBuilder: (context, index) {
                              final msg = state.messages[index];
                              final isOwn = msg.senderId == userId;
                              return _MessageBubble(
                                message: msg,
                                isOwn: isOwn,
                              );
                            },
                          ),
          ),
          // Input bar
          Container(
            padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              border: Border(
                top: BorderSide(color: theme.dividerColor),
              ),
            ),
            child: SafeArea(
              top: false,
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      maxLines: 3,
                      minLines: 1,
                      decoration: InputDecoration(
                        hintText: t.t('messages.typePlaceholder'),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(24),
                          borderSide: BorderSide(color: theme.dividerColor),
                        ),
                        contentPadding: const EdgeInsets.symmetric(
                            horizontal: 16, vertical: 10),
                        isDense: true,
                      ),
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _send(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    onPressed: state.sending ? null : _send,
                    icon: state.sending
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.send),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _send() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    _controller.clear();
    ref.read(chatProvider(widget.conversationId).notifier).sendMessage(text);
  }
}

class _MessageBubble extends StatelessWidget {
  final Message message;
  final bool isOwn;

  const _MessageBubble({required this.message, required this.isOwn});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    String timeStr = '';
    try {
      final dt = DateTime.parse(message.sentAt);
      timeStr = DateFormat.Hm().format(dt);
    } catch (_) {}

    return Align(
      alignment: isOwn ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.75,
        ),
        margin: const EdgeInsets.symmetric(vertical: 3),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: isOwn
              ? theme.colorScheme.primary
              : theme.colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isOwn ? 16 : 4),
            bottomRight: Radius.circular(isOwn ? 4 : 16),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              message.body,
              style: TextStyle(
                color: isOwn
                    ? theme.colorScheme.onPrimary
                    : theme.colorScheme.onSurface,
                fontSize: 14,
              ),
            ),
            const SizedBox(height: 4),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  timeStr,
                  style: TextStyle(
                    fontSize: 10,
                    color: isOwn
                        ? theme.colorScheme.onPrimary.withAlpha(180)
                        : theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                if (isOwn) ...[
                  const SizedBox(width: 4),
                  Icon(
                    Icons.done_all,
                    size: 14,
                    color: theme.colorScheme.onPrimary.withAlpha(180),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}
