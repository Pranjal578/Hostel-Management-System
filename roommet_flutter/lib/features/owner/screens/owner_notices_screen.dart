import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

class OwnerNoticesScreen extends ConsumerStatefulWidget {
  const OwnerNoticesScreen({super.key});
  @override
  ConsumerState<OwnerNoticesScreen> createState() => _OwnerNoticesScreenState();
}

class _OwnerNoticesScreenState extends ConsumerState<OwnerNoticesScreen> {
  List<dynamic> _notices = [];
  List<dynamic> _hostels = [];
  bool _loading = true;
  bool _showForm = false;
  int? _selectedHostelId;
  final _titleCtrl = TextEditingController();
  final _msgCtrl = TextEditingController();
  bool _posting = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final dash = await ApiService().getOwnerDashboard();
      final notices = await ApiService().getOwnerNotices();
      setState(() {
        _hostels = (dash['hostels'] as List? ?? []);
        _notices = notices;
        if (_hostels.isNotEmpty && _selectedHostelId == null) {
          _selectedHostelId = _hostels[0]['id'] as int?;
        }
        _loading = false;
      });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  Future<void> _post() async {
    if (_titleCtrl.text.isEmpty || _msgCtrl.text.isEmpty || _selectedHostelId == null) return;
    setState(() => _posting = true);
    await ApiService().postNotice(_selectedHostelId!, _titleCtrl.text.trim(), _msgCtrl.text.trim());
    _titleCtrl.clear();
    _msgCtrl.clear();
    setState(() { _posting = false; _showForm = false; });
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return GradientScaffold(
      appBar: RoommeetAppBar(title: 'Notices'),
      floatingActionButton: !_showForm
          ? FloatingActionButton.extended(
              onPressed: () => setState(() => _showForm = true),
              icon: const Icon(Icons.add),
              label: const Text('Post Notice'),
            )
          : null,
      child: _loading
          ? const ShimmerList(count: 4)
          : ListView(
              padding: const EdgeInsets.fromLTRB(16, kToolbarHeight + 24, 16, 120),
              children: [
                if (_showForm) _buildForm(),
                if (_notices.isEmpty)
                  const EmptyState(
                      icon: Icons.notifications_none_rounded,
                      title: 'No Notices Yet',
                      subtitle: 'Post a notice to inform your residents.')
                else ..._notices.map((n) => _NoticeTile(n as Map<String, dynamic>)),
              ],
            ),
    );
  }

  Widget _buildForm() {
    return GlassCard(
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text('Post New Notice',
                  style: TextStyle(
                      color: AppTheme.textPrimary,
                      fontSize: 16,
                      fontWeight: FontWeight.w600)),
              const Spacer(),
              IconButton(
                  icon: const Icon(Icons.close, color: AppTheme.textSecondary),
                  onPressed: () => setState(() => _showForm = false)),
            ],
          ),
          const SizedBox(height: 12),
          if (_hostels.length > 1)
            DropdownButtonFormField<int>(
              value: _selectedHostelId,
              dropdownColor: AppTheme.bgCard,
              style: const TextStyle(color: AppTheme.textPrimary),
              decoration: const InputDecoration(labelText: 'Select Hostel'),
              items: _hostels.map((h) => DropdownMenuItem<int>(
                value: h['id'] as int?,
                child: Text(h['name'] as String? ?? ''),
              )).toList(),
              onChanged: (v) => setState(() => _selectedHostelId = v),
            ),
          const SizedBox(height: 12),
          TextField(
            controller: _titleCtrl,
            style: const TextStyle(color: AppTheme.textPrimary),
            decoration: const InputDecoration(labelText: 'Title'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _msgCtrl,
            maxLines: 4,
            style: const TextStyle(color: AppTheme.textPrimary),
            decoration: const InputDecoration(
                labelText: 'Message',
                alignLabelWithHint: true),
          ),
          const SizedBox(height: 16),
          PrimaryButton(
              label: 'Post Notice',
              icon: Icons.send_rounded,
              onPressed: _post,
              isLoading: _posting),
        ],
      ),
    );
  }
}

class _NoticeTile extends StatelessWidget {
  final Map<String, dynamic> notice;
  const _NoticeTile(this.notice);
  @override
  Widget build(BuildContext context) {
    return GlassCard(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(notice['title'] ?? '',
              style: const TextStyle(
                  color: AppTheme.textPrimary,
                  fontSize: 15,
                  fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Text(notice['message'] ?? '',
              style: const TextStyle(
                  color: AppTheme.textSecondary, fontSize: 13, height: 1.5)),
          const SizedBox(height: 8),
          Text(notice['created_at'] ?? '',
              style: const TextStyle(color: AppTheme.textMuted, fontSize: 11)),
        ],
      ),
    );
  }
}
