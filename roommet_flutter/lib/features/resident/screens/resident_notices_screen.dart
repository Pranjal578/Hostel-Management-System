import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

final residentNoticesProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  return ApiService().getResidentNotices();
});

class ResidentNoticesScreen extends ConsumerWidget {
  const ResidentNoticesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final noticesAsync = ref.watch(residentNoticesProvider);

    return GradientScaffold(
      appBar: RoommeetAppBar(title: 'Notices'),
      child: noticesAsync.when(
        loading: () => const ShimmerList(count: 4),
        error: (e, _) => ErrorState(
          message: 'Could not load notices',
          onRetry: () => ref.invalidate(residentNoticesProvider),
        ),
        data: (notices) {
          if (notices.isEmpty) {
            return const EmptyState(
              icon: Icons.notifications_none_rounded,
              title: 'No Notices',
              subtitle: 'Your hostel owner has not posted any notices yet.',
            );
          }
          return RefreshIndicator(
            color: AppTheme.accent,
            onRefresh: () async => ref.invalidate(residentNoticesProvider),
            child: ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, kToolbarHeight + 24, 16, 24),
              itemCount: notices.length,
              itemBuilder: (_, i) {
                final n = notices[i] as Map<String, dynamic>;
                return GlassCard(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: AppTheme.accent.withOpacity(0.15),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: const Icon(Icons.campaign_rounded,
                                color: AppTheme.accent, size: 18),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              n['title'] ?? '',
                              style: const TextStyle(
                                  color: AppTheme.textPrimary,
                                  fontSize: 15,
                                  fontWeight: FontWeight.w600),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Text(
                        n['message'] ?? '',
                        style: const TextStyle(
                            color: AppTheme.textSecondary, fontSize: 14, height: 1.5),
                      ),
                      const SizedBox(height: 10),
                      Text(
                        n['created_at'] ?? '',
                        style: const TextStyle(
                            color: AppTheme.textMuted, fontSize: 11),
                      ),
                    ],
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
