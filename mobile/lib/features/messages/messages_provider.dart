/// Messages state management — conversations list + chat + announcements.
///
/// Reference: Phase 12B — Messaging providers
/// Includes offline cache for conversations and announcements.

import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/data/local_store/cache_store.dart';
import 'package:ecole_platform/domain/entities/conversation.dart';

// ── Conversations ──

class ConversationsState {
  final List<Conversation> items;
  final bool isLoading;
  final String? error;
  final String? nextCursor;
  final bool hasMore;
  final int unreadCount;

  const ConversationsState({
    this.items = const [],
    this.isLoading = false,
    this.error,
    this.nextCursor,
    this.hasMore = false,
    this.unreadCount = 0,
  });
}

class ConversationsNotifier extends StateNotifier<ConversationsState> {
  final Ref _ref;

  ConversationsNotifier(this._ref)
      : super(const ConversationsState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = const ConversationsState(isLoading: true);
    try {
      // Try cache first
      final cache = _ref.read(cacheStoreProvider);
      final cached = await cache.get('conversations:first');
      if (cached != null) {
        final items = cached.map((j) => Conversation.fromJson(j)).toList();
        state = ConversationsState(items: items);
        // Refresh in background
        _fetchFromApi();
        return;
      }
      await _fetchFromApi();
    } catch (e) {
      state = ConversationsState(error: e.toString());
    }
  }

  Future<void> _fetchFromApi() async {
    try {
      final api = _ref.read(apiClientProvider);
      final resp = await api.list('/messages/conversations', params: {'limit': '20'});
      final items = (resp['data'] as List<dynamic>)
          .map((j) => Conversation.fromJson(j as Map<String, dynamic>))
          .toList();

      // Cache
      final cache = _ref.read(cacheStoreProvider);
      await cache.put(
        'conversations:first',
        (resp['data'] as List<dynamic>).cast<Map<String, dynamic>>(),
        CacheTtl.notifications,
      );

      state = ConversationsState(
        items: items,
        nextCursor: resp['meta']?['next_cursor'] as String?,
        hasMore: resp['meta']?['has_more'] as bool? ?? false,
      );
    } catch (e) {
      if (state.items.isEmpty) {
        state = ConversationsState(error: e.toString());
      }
    }
  }

  Future<void> refresh() async {
    await _ref.read(cacheStoreProvider).invalidatePrefix('conversations:');
    await load();
  }

  void incrementUnread() {
    state = ConversationsState(
      items: state.items,
      nextCursor: state.nextCursor,
      hasMore: state.hasMore,
      unreadCount: state.unreadCount + 1,
    );
  }

  void resetUnread() {
    state = ConversationsState(
      items: state.items,
      nextCursor: state.nextCursor,
      hasMore: state.hasMore,
      unreadCount: 0,
    );
  }
}

final conversationsProvider =
    StateNotifierProvider<ConversationsNotifier, ConversationsState>((ref) {
  return ConversationsNotifier(ref);
});

// ── Chat (single conversation) ──

class ChatState {
  final List<Message> messages;
  final bool isLoading;
  final String? error;
  final bool sending;

  const ChatState({
    this.messages = const [],
    this.isLoading = false,
    this.error,
    this.sending = false,
  });
}

class ChatNotifier extends StateNotifier<ChatState> {
  final Ref _ref;
  final String conversationId;

  ChatNotifier(this._ref, this.conversationId)
      : super(const ChatState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = const ChatState(isLoading: true);
    try {
      final api = _ref.read(apiClientProvider);
      final resp = await api.list(
        '/messages/conversations/$conversationId/messages',
        params: {'limit': '50'},
      );
      final messages = (resp['data'] as List<dynamic>)
          .map((j) => Message.fromJson(j as Map<String, dynamic>))
          .toList()
          .reversed
          .toList();

      state = ChatState(messages: messages);

      // Mark as read
      if (messages.isNotEmpty) {
        final newestId = (resp['data'] as List<dynamic>).first['id'] as String;
        api.post('/messages/conversations/$conversationId/read', body: {'message_id': newestId}).catchError((_) {});
      }
    } catch (e) {
      state = ChatState(error: e.toString());
    }
  }

  Future<void> sendMessage(String body) async {
    state = ChatState(messages: state.messages, sending: true);
    try {
      final api = _ref.read(apiClientProvider);
      final resp = await api.post(
        '/messages/conversations/$conversationId/messages',
        body: {'body': body},
      );
      final msg = Message.fromJson(resp['data'] as Map<String, dynamic>);
      state = ChatState(messages: [...state.messages, msg]);
    } catch (e) {
      state = ChatState(messages: state.messages, error: e.toString());
    }
  }

  void addIncomingMessage(Message msg) {
    if (msg.conversationId == conversationId) {
      state = ChatState(messages: [...state.messages, msg]);
    }
  }
}

final chatProvider = StateNotifierProvider.family<ChatNotifier, ChatState, String>(
  (ref, conversationId) => ChatNotifier(ref, conversationId),
);

// ── Announcements ──

class AnnouncementsState {
  final List<Announcement> items;
  final bool isLoading;
  final String? error;
  final String? nextCursor;
  final bool hasMore;

  const AnnouncementsState({
    this.items = const [],
    this.isLoading = false,
    this.error,
    this.nextCursor,
    this.hasMore = false,
  });
}

class AnnouncementsNotifier extends StateNotifier<AnnouncementsState> {
  final Ref _ref;

  AnnouncementsNotifier(this._ref)
      : super(const AnnouncementsState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = const AnnouncementsState(isLoading: true);
    try {
      // Try cache
      final cache = _ref.read(cacheStoreProvider);
      final cached = await cache.get('announcements:first');
      if (cached != null) {
        final items = cached.map((j) => Announcement.fromJson(j)).toList();
        state = AnnouncementsState(items: items);
        _fetchFromApi();
        return;
      }
      await _fetchFromApi();
    } catch (e) {
      state = AnnouncementsState(error: e.toString());
    }
  }

  Future<void> _fetchFromApi() async {
    try {
      final api = _ref.read(apiClientProvider);
      final resp = await api.list('/announcements', params: {'limit': '20'});
      final items = (resp['data'] as List<dynamic>)
          .map((j) => Announcement.fromJson(j as Map<String, dynamic>))
          .toList();

      final cache = _ref.read(cacheStoreProvider);
      await cache.put(
        'announcements:first',
        (resp['data'] as List<dynamic>).cast<Map<String, dynamic>>(),
        CacheTtl.feed,
      );

      state = AnnouncementsState(
        items: items,
        nextCursor: resp['meta']?['next_cursor'] as String?,
        hasMore: resp['meta']?['has_more'] as bool? ?? false,
      );
    } catch (e) {
      if (state.items.isEmpty) {
        state = AnnouncementsState(error: e.toString());
      }
    }
  }

  Future<void> refresh() async {
    await _ref.read(cacheStoreProvider).invalidatePrefix('announcements:');
    await load();
  }
}

final announcementsProvider =
    StateNotifierProvider<AnnouncementsNotifier, AnnouncementsState>((ref) {
  return AnnouncementsNotifier(ref);
});
