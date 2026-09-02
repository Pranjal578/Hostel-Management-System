import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

final adminShopsProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  return ApiService().getAdminShops();
});

class AdminShopsScreen extends ConsumerWidget {
  const AdminShopsScreen({super.key});

  Future<void> _verify(BuildContext context, WidgetRef ref, int shopId, String action, String shopName) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppTheme.bgCard,
        title: Text('${action == 'approve' ? 'Approve' : 'Reject'} $shopName',
            style: const TextStyle(color: AppTheme.textPrimary)),
        content: Text('Are you sure you want to $action this pharmacy shop?',
            style: const TextStyle(color: AppTheme.textSecondary)),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel', style: TextStyle(color: AppTheme.textSecondary))),
          ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: action == 'approve' ? AppTheme.success : AppTheme.danger,
              ),
              onPressed: () => Navigator.pop(context, true),
              child: Text(action == 'approve' ? 'Approve' : 'Reject')),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        await ApiService().verifyShop(shopId, action);
        ref.invalidate(adminShopsProvider);
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Shop $shopName ${action}d successfully.')),
          );
        }
      } catch (e) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Verification failed: $e')),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(adminShopsProvider);
    return GradientScaffold(
      appBar: RoommeetAppBar(title: 'Medical Stores'),
      child: async.when(
        loading: () => const ShimmerList(),
        error: (e, _) => ErrorState(message: e.toString(), onRetry: () => ref.invalidate(adminShopsProvider)),
        data: (shops) => shops.isEmpty
            ? const EmptyState(icon: Icons.storefront_outlined, title: 'No Shops Registered', subtitle: 'No medical shops are currently registered.')
            : ListView.builder(
                padding: const EdgeInsets.fromLTRB(16, kToolbarHeight + 24, 16, 24),
                itemCount: shops.length,
                itemBuilder: (_, i) {
                  final s = shops[i] as Map<String, dynamic>;
                  final status = s['verification_status'] as String? ?? 'Pending';
                  final isPending = status == 'Pending';

                  return GlassCard(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            CircleAvatar(
                              radius: 20,
                              backgroundColor: AppTheme.success.withOpacity(0.15),
                              child: const Icon(Icons.storefront_rounded, color: AppTheme.success),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(s['name'] ?? '',
                                      style: const TextStyle(color: AppTheme.textPrimary, fontSize: 15, fontWeight: FontWeight.w600)),
                                  Text(s['location'] ?? '', style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                                ],
                              ),
                            ),
                            StatusBadge(status),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            const Icon(Icons.email_outlined, size: 14, color: AppTheme.textMuted),
                            const SizedBox(width: 6),
                            Text(s['owner_email'] ?? '', style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                            const Spacer(),
                            const Icon(Icons.star_rounded, size: 14, color: Colors.amber),
                            const SizedBox(width: 4),
                            Text('${s['rating_avg'] ?? 0.0}',
                                style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13, fontWeight: FontWeight.w600)),
                          ],
                        ),
                        if (isPending) ...[
                          const SizedBox(height: 14),
                          Row(
                            children: [
                              Expanded(
                                child: PrimaryButton(
                                  label: 'Approve',
                                  icon: Icons.check_circle_rounded,
                                  onPressed: () => _verify(context, ref, s['id'] as int, 'approve', s['name'] as String),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: DangerButton(
                                  label: 'Reject',
                                  onPressed: () => _verify(context, ref, s['id'] as int, 'reject', s['name'] as String),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ],
                    ),
                  );
                },
              ),
      ),
    );
  }
}
