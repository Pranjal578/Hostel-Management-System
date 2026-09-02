import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

class ResidentChatScreen extends ConsumerStatefulWidget {
  const ResidentChatScreen({super.key});
  @override
  ConsumerState<ResidentChatScreen> createState() => _ResidentChatScreenState();
}

class _ResidentChatScreenState extends ConsumerState<ResidentChatScreen> {
  List<dynamic>? _contacts;
  Map<String, dynamic>? _activeContact;
  List<dynamic> _messages = [];
  bool _loadingContacts = true;
  bool _loadingMessages = false;
  final _msgCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  Timer? _pollTimer;
  int? _myUserId;

  @override
  void initState() {
    super.initState();
    _loadContacts();
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _msgCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadContacts() async {
    try {
      final contacts = await ApiService().getChatContacts();
      final me = await ApiService().getMe();
      setState(() {
        _contacts = contacts;
        _loadingContacts = false;
        _myUserId = me['id'] as int?;
      });
      if (contacts.isNotEmpty) _selectContact(contacts[0] as Map<String, dynamic>);
    } catch (_) {
      setState(() => _loadingContacts = false);
    }
  }

  void _selectContact(Map<String, dynamic> contact) {
    setState(() {
      _activeContact = contact;
      _loadingMessages = true;
    });
    _loadMessages();
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 4), (_) => _loadMessages());
  }

  Future<void> _loadMessages() async {
    final recipientId = _activeContact?['user_id'] as int?;
    if (recipientId == null) return;
    try {
      final msgs = await ApiService().getChatMessages(recipientId);
      if (mounted) {
        setState(() { _messages = msgs; _loadingMessages = false; });
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (_scrollCtrl.hasClients) {
            _scrollCtrl.animateTo(
              _scrollCtrl.position.maxScrollExtent,
              duration: const Duration(milliseconds: 200),
              curve: Curves.easeOut,
            );
          }
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loadingMessages = false);
    }
  }

  Future<void> _send() async {
    final content = _msgCtrl.text.trim();
    if (content.isEmpty) return;
    final recipientId = _activeContact?['user_id'] as int?;
    if (recipientId == null) return;
    _msgCtrl.clear();
    await ApiService().sendMessage(recipientId, content);
    _loadMessages();
  }

  @override
  Widget build(BuildContext context) {
    return GradientScaffold(
      appBar: RoommeetAppBar(
        title: _activeContact != null
            ? _activeContact!['name'] as String? ?? 'Chat'
            : 'Chat',
      ),
      child: _loadingContacts
          ? const ShimmerList(count: 3)
          : _contacts == null || _contacts!.isEmpty
              ? const EmptyState(
                  icon: Icons.chat_bubble_outline_rounded,
                  title: 'No Contacts',
                  subtitle: 'You have no one to chat with yet.',
                )
              : Column(
                  children: [
                    SizedBox(height: kToolbarHeight + 16),
                    Expanded(child: _buildMessages()),
                    _buildInputBar(),
                    const SizedBox(height: 80),
                  ],
                ),
    );
  }

  Widget _buildMessages() {
    if (_loadingMessages) return const ShimmerList(count: 5, itemHeight: 60);
    if (_messages.isEmpty) {
      return const Center(
        child: Text('Start the conversation!',
            style: TextStyle(color: AppTheme.textMuted)),
      );
    }
    return ListView.builder(
      controller: _scrollCtrl,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      itemCount: _messages.length,
      itemBuilder: (_, i) {
        final m = _messages[i] as Map<String, dynamic>;
        final isMe = (m['sender_id'] as int?) == _myUserId;
        return _MessageBubble(message: m, isMe: isMe);
      },
    );
  }

  Widget _buildInputBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        border: Border(top: BorderSide(color: AppTheme.divider)),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _msgCtrl,
              style: const TextStyle(color: AppTheme.textPrimary, fontSize: 14),
              decoration: InputDecoration(
                hintText: 'Type a message…',
                filled: true,
                fillColor: AppTheme.bgSurface,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16, vertical: 10),
              ),
              onSubmitted: (_) => _send(),
            ),
          ),
          const SizedBox(width: 10),
          GestureDetector(
            onTap: _send,
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                gradient: AppTheme.accentGradient,
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                      color: AppTheme.accent.withOpacity(0.4),
                      blurRadius: 12),
                ],
              ),
              child: const Icon(Icons.send_rounded, color: Colors.white, size: 20),
            ),
          ),
        ],
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  final Map<String, dynamic> message;
  final bool isMe;
  const _MessageBubble({required this.message, required this.isMe});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        constraints: BoxConstraints(
            maxWidth: MediaQuery.of(context).size.width * 0.72),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          gradient: isMe ? AppTheme.accentGradient : null,
          color: isMe ? null : AppTheme.bgSurface,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: isMe ? const Radius.circular(16) : Radius.zero,
            bottomRight: isMe ? Radius.zero : const Radius.circular(16),
          ),
        ),
        child: Column(
          crossAxisAlignment:
              isMe ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            Text(
              message['message_content'] as String? ?? '',
              style: TextStyle(
                  color: isMe ? Colors.white : AppTheme.textPrimary,
                  fontSize: 14),
            ),
            const SizedBox(height: 4),
            Text(
              message['created_at'] as String? ?? '',
              style: TextStyle(
                  color: isMe
                      ? Colors.white.withOpacity(0.6)
                      : AppTheme.textMuted,
                  fontSize: 10),
            ),
          ],
        ),
      ),
    );
  }
}
