import 'package:flutter/material.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

class AdminResidentsScreen extends StatefulWidget {
  const AdminResidentsScreen({super.key});
  @override
  State<AdminResidentsScreen> createState() => _AdminResidentsScreenState();
}

class _AdminResidentsScreenState extends State<AdminResidentsScreen> {
  List<dynamic> _residents = [];
  bool _loading = true;
  final _searchCtrl = TextEditingController();

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load({String? q}) async {
    setState(() => _loading = true);
    final data = await ApiService().getAdminResidents(search: q);
    setState(() { _residents = data['residents'] as List? ?? []; _loading = false; });
  }

  @override
  Widget build(BuildContext context) {
    return GradientScaffold(
      appBar: RoommeetAppBar(title: 'All Residents'),
      child: Column(
        children: [
          SizedBox(height: kToolbarHeight + 16),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: TextField(
              controller: _searchCtrl,
              style: const TextStyle(color: AppTheme.textPrimary, fontSize: 14),
              decoration: InputDecoration(
                hintText: 'Search by name, room, hostel…',
                prefixIcon: const Icon(Icons.search_rounded, color: AppTheme.textSecondary, size: 20),
                suffixIcon: _searchCtrl.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.close_rounded, size: 18, color: AppTheme.textSecondary),
                        onPressed: () { _searchCtrl.clear(); _load(); })
                    : null,
              ),
              onChanged: (v) => _load(q: v.isEmpty ? null : v),
            ),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: _loading
                ? const ShimmerList()
                : _residents.isEmpty
                    ? const EmptyState(icon: Icons.people_outline_rounded, title: 'No Residents', subtitle: 'No results found.')
                    : ListView.builder(
                        padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
                        itemCount: _residents.length,
                        itemBuilder: (_, i) {
                          final r = _residents[i] as Map<String, dynamic>;
                          return GlassCard(
                            margin: const EdgeInsets.only(bottom: 8),
                            padding: const EdgeInsets.all(12),
                            child: Row(
                              children: [
                                CircleAvatar(
                                  radius: 18,
                                  backgroundColor: AppTheme.accent.withOpacity(0.15),
                                  child: Text((r['full_name'] ?? '?')[0].toUpperCase(),
                                      style: const TextStyle(color: AppTheme.accent, fontWeight: FontWeight.w700, fontSize: 13)),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(r['full_name'] ?? '', style: const TextStyle(color: AppTheme.textPrimary, fontSize: 14, fontWeight: FontWeight.w600)),
                                      Text('${r['hostel_name'] ?? ''} · Room ${r['room_number'] ?? 'Pending'}',
                                          style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                                    ],
                                  ),
                                ),
                                StatusBadge(r['status'] ?? 'Pending'),
                              ],
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}
