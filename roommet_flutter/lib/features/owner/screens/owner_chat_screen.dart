import 'dart:async';
import 'package:flutter/material.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

class OwnerChatScreen extends StatefulWidget {
  const OwnerChatScreen({super.key});
  @override
  State<OwnerChatScreen> createState() => _OwnerChatScreenState();
}

class _OwnerChatScreenState extends State<OwnerChatScreen> {
  List<dynamic> _contacts = [];
  Map<String, dynamic>? _active;
  List<dynamic> _messages = [];
  bool _loadingContacts = true;
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
    final contacts = await ApiService().getChatContacts();
    final me = await ApiService().getMe();
    setState(() {
      _contacts = contacts;
      _myUserId = me['id'] as int?;
      _loadingContacts = false;
    });
  }

  void _select(Map<String, dynamic> contact) {
    setState(() { _active = contact; _messages = []; });
    _pollTimer?.cancel();
    _loadMessages();
    _pollTimer = Timer.periodic(const Duration(seconds: 4), (_) => _loadMessages());
  }

  Future<void> _loadMessages() async {
    final id = _active?['user_id'] as int?;
    if (id == null) return;
    final msgs = await ApiService().getChatMessages(id);
    if (mounted) {
      setState(() => _messages = msgs);
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scrollCtrl.hasClients) {
          _scrollCtrl.animateTo(_scrollCtrl.position.maxScrollExtent,
              duration: const Duration(milliseconds: 200), curve: Curves.easeOut);
        }
      });
    }
  }

  Future<void> _send() async {
    final content = _msgCtrl.text.trim();
    if (content.isEmpty) return;
    final id = _active?['user_id'] as int?;
    if (id == null) return;
    _msgCtrl.clear();
    await ApiService().sendMessage(id, content);
    _loadMessages();
  }

  @override
  Widget build(BuildContext context) {
    return GradientScaffold(
      appBar: RoommeetAppBar(
          title: _active != null ? _active!['name'] as String? ?? 'Chat' : 'Chat'),
      child: _loadingContacts
          ? const ShimmerList()
          : Row(
              children: [
                // Contact sidebar (if multiple residents)
                if (_contacts.length > 1)
                  Container(
                    width: 80,
                    margin: const EdgeInsets.only(top: kToolbarHeight + 16),
                    child: ListView.builder(
                      itemCount: _contacts.length,
                      itemBuilder: (_, i) {
                        final c = _contacts[i] as Map<String, dynamic>;
                        final isActive = _active?['user_id'] == c['user_id'];
                        final unread = c['unread_count'] as int? ?? 0;
                        return GestureDetector(
                          onTap: () => _select(c),
                          child: Container(
                            margin: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 4),
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: isActive
                                  ? AppTheme.accent.withOpacity(0.2)
                                  : Colors.transparent,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Stack(
                              alignment: Alignment.topRight,
                              children: [
                                CircleAvatar(
                                  radius: 22,
                                  backgroundColor:
                                      AppTheme.accent.withOpacity(0.2),
                                  child: Text(
                                    (c['name'] as String? ?? '?')[0].toUpperCase(),
                                    style: const TextStyle(
                                        color: AppTheme.accent,
                                        fontWeight: FontWeight.w700),
                                  ),
                                ),
                                if (unread > 0)
                                  Container(
                                    padding: const EdgeInsets.all(4),
                                    decoration: const BoxDecoration(
                                        color: AppTheme.danger,
                                        shape: BoxShape.circle),
                                    child: Text('$unread',
                                        style: const TextStyle(
                                            color: Colors.white,
                                            fontSize: 9,
                                            fontWeight: FontWeight.w700)),
                                  ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                // Chat panel
                Expanded(
                  child: _active == null
                      ? const Center(
                          child: Text('Select a resident to chat',
                              style: TextStyle(color: AppTheme.textMuted)))
                      : Column(
                          children: [
                            SizedBox(height: kToolbarHeight + 16),
                            Expanded(
                              child: _messages.isEmpty
                                  ? const Center(
                                      child: Text('Start the conversation!',
                                          style: TextStyle(
                                              color: AppTheme.textMuted)))
                                  : ListView.builder(
                                      controller: _scrollCtrl,
                                      padding: const EdgeInsets.symmetric(
                                          horizontal: 12, vertical: 8),
                                      itemCount: _messages.length,
                                      itemBuilder: (_, i) {
                                        final m = _messages[i]
                                            as Map<String, dynamic>;
                                        final isMe =
                                            (m['sender_id'] as int?) == _myUserId;
                                        return _Bubble(m: m, isMe: isMe);
                                      },
                                    ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 12, vertical: 8),
                              decoration: BoxDecoration(
                                  color: AppTheme.bgCard,
                                  border: Border(
                                      top: BorderSide(
                                          color: AppTheme.divider))),
                              child: Row(
                                children: [
                                  Expanded(
                                    child: TextField(
                                      controller: _msgCtrl,
                                      style: const TextStyle(
                                          color: AppTheme.textPrimary,
                                          fontSize: 14),
                                      decoration: InputDecoration(
                                        hintText: 'Message…',
                                        filled: true,
                                        fillColor: AppTheme.bgSurface,
                                        border: OutlineInputBorder(
                                          borderRadius:
                                              BorderRadius.circular(24),
                                          borderSide: BorderSide.none,
                                        ),
                                        contentPadding:
                                            const EdgeInsets.symmetric(
                                                horizontal: 16, vertical: 10),
                                      ),
                                      onSubmitted: (_) => _send(),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  GestureDetector(
                                    onTap: _send,
                                    child: Container(
                                      padding: const EdgeInsets.all(11),
                                      decoration: BoxDecoration(
                                        gradient: AppTheme.accentGradient,
                                        shape: BoxShape.circle,
                                      ),
                                      child: const Icon(Icons.send_rounded,
                                          color: Colors.white, size: 18),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 80),
                          ],
                        ),
                ),
              ],
            ),
    );
  }
}

class _Bubble extends StatelessWidget {
  final Map<String, dynamic> m;
  final bool isMe;
  const _Bubble({required this.m, required this.isMe});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 3),
        constraints:
            BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.65),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          gradient: isMe ? AppTheme.accentGradient : null,
          color: isMe ? null : AppTheme.bgSurface,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(14),
            topRight: const Radius.circular(14),
            bottomLeft: isMe ? const Radius.circular(14) : Radius.zero,
            bottomRight: isMe ? Radius.zero : const Radius.circular(14),
          ),
        ),
        child: Text(m['message_content'] as String? ?? '',
            style: TextStyle(
                color: isMe ? Colors.white : AppTheme.textPrimary,
                fontSize: 13)),
      ),
    );
  }
}
