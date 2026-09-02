import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

class OwnerResidentsScreen extends ConsumerStatefulWidget {
  const OwnerResidentsScreen({super.key});
  @override
  ConsumerState<OwnerResidentsScreen> createState() => _OwnerResidentsScreenState();
}

class _OwnerResidentsScreenState extends ConsumerState<OwnerResidentsScreen> {
  List<dynamic> _residents = [];
  bool _loading = true;
  String _search = '';
  String _statusFilter = '';
  int _page = 1;
  int _totalPages = 1;
  final _searchCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load({bool reset = false}) async {
    if (reset) setState(() { _page = 1; _residents = []; });
    setState(() => _loading = true);
    try {
      final data = await ApiService().getOwnerResidents(
        page: _page, search: _search, status: _statusFilter);
      setState(() {
        _residents = data['residents'] as List? ?? [];
        _totalPages = data['pages'] as int? ?? 1;
        _loading = false;
      });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  Future<void> _approve(int residentId, String name) async {
    final roomCtrl = TextEditingController();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppTheme.bgCard,
        title: Text('Approve $name',
            style: const TextStyle(color: AppTheme.textPrimary)),
        content: TextField(
          controller: roomCtrl,
          style: const TextStyle(color: AppTheme.textPrimary),
          decoration: const InputDecoration(labelText: 'Assign Room Number'),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel',
                  style: TextStyle(color: AppTheme.textSecondary))),
          ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Approve')),
        ],
      ),
    );
    if (confirmed == true) {
      await ApiService().approveResident(residentId,
          roomNumber: roomCtrl.text.trim().isEmpty ? null : roomCtrl.text.trim());
      _load(reset: true);
    }
  }

  Future<void> _reject(int residentId) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppTheme.bgCard,
        title: const Text('Reject Resident',
            style: TextStyle(color: AppTheme.textPrimary)),
        content: const Text('Are you sure you want to reject this resident?',
            style: TextStyle(color: AppTheme.textSecondary)),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel',
                  style: TextStyle(color: AppTheme.textSecondary))),
          ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.danger),
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Reject')),
        ],
      ),
    );
    if (confirmed == true) {
      await ApiService().rejectResident(residentId);
      _load(reset: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return GradientScaffold(
      appBar: RoommeetAppBar(title: 'Residents'),
      child: Column(
        children: [
          SizedBox(height: kToolbarHeight + 16),
          // ── Search + Filter ──────────────────────
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _searchCtrl,
                    style: const TextStyle(color: AppTheme.textPrimary, fontSize: 14),
                    decoration: InputDecoration(
                      hintText: 'Search by name or room…',
                      prefixIcon: const Icon(Icons.search_rounded,
                          color: AppTheme.textSecondary, size: 20),
                      suffixIcon: _search.isNotEmpty
                          ? IconButton(
                              icon: const Icon(Icons.close_rounded,
                                  color: AppTheme.textSecondary, size: 18),
                              onPressed: () {
                                _searchCtrl.clear();
                                setState(() => _search = '');
                                _load(reset: true);
                              },
                            )
                          : null,
                    ),
                    onChanged: (v) {
                      setState(() => _search = v);
                      _load(reset: true);
                    },
                  ),
                ),
                const SizedBox(width: 10),
                PopupMenuButton<String>(
                  color: AppTheme.bgCard,
                  icon: const Icon(Icons.filter_list_rounded,
                      color: AppTheme.textSecondary),
                  onSelected: (v) {
                    setState(() => _statusFilter = v);
                    _load(reset: true);
                  },
                  itemBuilder: (_) => [
                    const PopupMenuItem(value: '', child: Text('All')),
                    const PopupMenuItem(value: 'Active', child: Text('Active')),
                    const PopupMenuItem(value: 'Pending', child: Text('Pending')),
                    const PopupMenuItem(value: 'Rejected', child: Text('Rejected')),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          // ── List ──────────────────────────────────
          Expanded(
            child: _loading
                ? const ShimmerList(count: 6)
                : _residents.isEmpty
                    ? const EmptyState(
                        icon: Icons.people_outline_rounded,
                        title: 'No Residents Found',
                        subtitle: 'Try adjusting your search or filter.')
                    : RefreshIndicator(
                        color: AppTheme.accent,
                        onRefresh: () => _load(reset: true),
                        child: ListView.builder(
                          padding: const EdgeInsets.fromLTRB(16, 0, 16, 100),
                          itemCount: _residents.length,
                          itemBuilder: (_, i) {
                            final r = _residents[i] as Map<String, dynamic>;
                            return _ResidentTile(
                              resident: r,
                              onApprove: () => _approve(r['id'] as int, r['full_name'] as String),
                              onReject: () => _reject(r['id'] as int),
                            );
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }
}

class _ResidentTile extends StatelessWidget {
  final Map<String, dynamic> resident;
  final VoidCallback onApprove;
  final VoidCallback onReject;
  const _ResidentTile(
      {required this.resident, required this.onApprove, required this.onReject});

  @override
  Widget build(BuildContext context) {
    final status = resident['status'] as String? ?? 'Pending';
    final isPending = status == 'Pending';
    return GlassCard(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 20,
                backgroundColor: AppTheme.accent.withOpacity(0.2),
                child: Text(
                  (resident['full_name'] as String? ?? '?')[0].toUpperCase(),
                  style: const TextStyle(
                      color: AppTheme.accent, fontWeight: FontWeight.w700),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(resident['full_name'] ?? '',
                        style: const TextStyle(
                            color: AppTheme.textPrimary,
                            fontSize: 15,
                            fontWeight: FontWeight.w600)),
                    Text(resident['email'] ?? '',
                        style: const TextStyle(
                            color: AppTheme.textSecondary, fontSize: 12)),
                  ],
                ),
              ),
              StatusBadge(status),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              _chip(Icons.meeting_room_rounded,
                  'Room ${resident['room_number'] ?? 'Pending'}'),
              const SizedBox(width: 8),
              _chip(Icons.home_work_rounded, resident['hostel_name'] ?? ''),
              const SizedBox(width: 8),
              _chip(Icons.payment_rounded, resident['payment_status'] ?? 'None'),
            ],
          ),
          if (isPending) ...[
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: PrimaryButton(
                    label: 'Approve',
                    icon: Icons.check_circle_rounded,
                    onPressed: onApprove,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(child: DangerButton(label: 'Reject', onPressed: onReject)),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _chip(IconData icon, String label) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: AppTheme.bgSurface,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 11, color: AppTheme.textMuted),
            const SizedBox(width: 4),
            Text(label,
                style: const TextStyle(color: AppTheme.textMuted, fontSize: 11)),
          ],
        ),
      );
}
