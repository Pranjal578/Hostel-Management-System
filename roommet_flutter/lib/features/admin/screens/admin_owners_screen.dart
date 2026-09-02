import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

final adminOwnersProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  return ApiService().getAdminOwners();
});

class AdminOwnersScreen extends ConsumerWidget {
  const AdminOwnersScreen({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(adminOwnersProvider);
    return GradientScaffold(
      appBar: RoommeetAppBar(title: 'Hostel Owners'),
      child: async.when(
        loading: () => const ShimmerList(),
        error: (e, _) => ErrorState(message: e.toString(), onRetry: () => ref.invalidate(adminOwnersProvider)),
        data: (owners) => owners.isEmpty
            ? const EmptyState(icon: Icons.person_off_rounded, title: 'No Owners', subtitle: 'No hostel owners registered yet.')
            : ListView.builder(
                padding: const EdgeInsets.fromLTRB(16, kToolbarHeight + 24, 16, 24),
                itemCount: owners.length,
                itemBuilder: (_, i) {
                  final o = owners[i] as Map<String, dynamic>;
                  return GlassCard(
                    margin: const EdgeInsets.only(bottom: 10),
                    padding: const EdgeInsets.all(14),
                    child: Row(
                      children: [
                        CircleAvatar(
                          radius: 22,
                          backgroundColor: AppTheme.info.withOpacity(0.2),
                          child: Text((o['full_name'] ?? o['email'] ?? '?')[0].toUpperCase(),
                              style: const TextStyle(color: AppTheme.info, fontWeight: FontWeight.w700)),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(o['full_name'] ?? o['email'] ?? '',
                                  style: const TextStyle(color: AppTheme.textPrimary, fontSize: 15, fontWeight: FontWeight.w600)),
                              Text(o['email'] ?? '', style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                            ],
                          ),
                        ),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text('${o['hostel_count'] ?? 0}', style: const TextStyle(color: AppTheme.accent, fontSize: 20, fontWeight: FontWeight.w700)),
                            const Text('Hostels', style: TextStyle(color: AppTheme.textMuted, fontSize: 11)),
                          ],
                        ),
                      ],
                    ),
                  );
                },
              ),
      ),
    );
  }
}
