/// Conversations screen — inbox with unread badges.
///
/// Reference: Phase 12B — Messaging inbox

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/conversation.dart';
import 'messages_provider.dart';

class ConversationsScreen extends ConsumerWidget {
  const ConversationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(conversationsProvider);
    final t = AppLocalizations.of(ref);
    final userId = ref.watch(authProvider).user?.id ?? '';

    return Scaffold(
      appBar: AppBar(title: Text(t.t('messages.title'))),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showNewConversation(context, ref, t),
        child: const Icon(Icons.edit),
      ),
      body: _buildBody(context, ref, state, t, userId),
    );
  }

  Widget _buildBody(BuildContext context, WidgetRef ref,
      ConversationsState state, AppLocalizations t, String userId) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.error != null && state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text(state.error!),
            const SizedBox(height: 16),
            FilledButton.tonal(
              onPressed: () => ref.read(conversationsProvider.notifier).load(),
              child: Text(t.t('common.retry')),
            ),
          ],
        ),
      );
    }
    if (state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.chat_bubble_outline, size: 48, color: Colors.grey),
            const SizedBox(height: 16),
            Text(t.t('messages.empty')),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(conversationsProvider.notifier).refresh(),
      child: ListView.builder(
        itemCount: state.items.length,
        itemBuilder: (context, index) {
          final conv = state.items[index];
          return _ConversationTile(
            conversation: conv,
            userId: userId,
            t: t,
            onTap: () => context.push('/messages/${conv.id}'),
          );
        },
      ),
    );
  }

  void _showNewConversation(
      BuildContext context, WidgetRef ref, AppLocalizations t) {
    final recipientCtrl = TextEditingController();
    final subjectCtrl = TextEditingController();
    final messageCtrl = TextEditingController();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => Padding(
        padding: EdgeInsets.fromLTRB(
            16, 24, 16, MediaQuery.of(ctx).viewInsets.bottom + 16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(t.t('messages.newConversation'),
                style: Theme.of(ctx).textTheme.titleLarge),
            const SizedBox(height: 16),
            TextField(
              controller: recipientCtrl,
              decoration: InputDecoration(
                labelText: t.t('messages.recipient'),
                border: const OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: subjectCtrl,
              decoration: InputDecoration(
                labelText: t.t('messages.subject'),
                border: const OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: messageCtrl,
              maxLines: 3,
              decoration: InputDecoration(
                labelText: t.t('messages.message'),
                border: const OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () async {
                  if (recipientCtrl.text.isEmpty || messageCtrl.text.isEmpty)
                    return;
                  try {
                    final api = ref.read(apiClientProvider);
                    final resp =
                        await api.post('/messages/conversations', body: {
                      'type': 'DIRECT',
                      'participant_ids': [recipientCtrl.text.trim()],
                      'subject':
                          subjectCtrl.text.isNotEmpty ? subjectCtrl.text : null,
                      'initial_message': messageCtrl.text,
                    });
                    final convId = resp.data['id'] as String;
                    if (ctx.mounted) Navigator.pop(ctx);
                    if (context.mounted) context.push('/messages/$convId');
                  } catch (e) {
                    if (ctx.mounted) {
                      ScaffoldMessenger.of(ctx).showSnackBar(
                        SnackBar(content: Text(e.toString())),
                      );
                    }
                  }
                },
                child: Text(t.t('messages.send')),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ConversationTile extends StatelessWidget {
  final Conversation conversation;
  final String userId;
  final AppLocalizations t;
  final VoidCallback onTap;

  const _ConversationTile({
    required this.conversation,
    required this.userId,
    required this.t,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final subtitle = conversation.type == 'DIRECT'
        ? t.t('messages.direct')
        : '${t.t('messages.group')} · ${conversation.participants.length} ${t.t('messages.participants')}';

    String dateStr = '';
    final dateSource = conversation.lastMessageAt ?? conversation.createdAt;
    try {
      final dt = DateTime.parse(dateSource);
      dateStr = DateFormat.MMMd('fr').add_Hm().format(dt);
    } catch (_) {}

    return ListTile(
      leading: CircleAvatar(
        backgroundColor: theme.colorScheme.primaryContainer,
        child: Icon(
          conversation.type == 'DIRECT' ? Icons.person : Icons.group,
          color: theme.colorScheme.onPrimaryContainer,
        ),
      ),
      title: Text(
        conversation.subject ?? _otherParticipant(),
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: TextStyle(
          fontWeight:
              conversation.unreadCount > 0 ? FontWeight.w800 : FontWeight.w600,
        ),
      ),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (conversation.lastMessageBody != null)
            Text(
              conversation.lastMessageBody!.length > 50
                  ? '${conversation.lastMessageBody!.substring(0, 50)}...'
                  : conversation.lastMessageBody!,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: theme.textTheme.bodySmall?.copyWith(
                fontWeight:
                    conversation.unreadCount > 0 ? FontWeight.w600 : null,
              ),
            ),
          Text(subtitle,
              style: theme.textTheme.bodySmall?.copyWith(fontSize: 11)),
        ],
      ),
      trailing: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Text(dateStr, style: theme.textTheme.bodySmall),
          if (conversation.unreadCount > 0) ...[
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: theme.colorScheme.primary,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                '${conversation.unreadCount}',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  color: theme.colorScheme.onPrimary,
                ),
              ),
            ),
          ],
        ],
      ),
      onTap: onTap,
    );
  }

  String _otherParticipant() {
    final other =
        conversation.participants.where((p) => p.userId != userId).firstOrNull;
    if (other != null) return '${other.userId.substring(0, 8)}...';
    return t.t('messages.conversation');
  }
}
