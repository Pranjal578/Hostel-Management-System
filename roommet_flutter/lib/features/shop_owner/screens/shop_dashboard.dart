import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/features/auth/providers/auth_provider.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

import 'package:roommet_flutter/shared/widgets/app_drawer.dart';

final shopDashboardProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  return ApiService().getShopDashboard();
});

class ShopDashboard extends ConsumerWidget {
  const ShopDashboard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashAsync = ref.watch(shopDashboardProvider);

    return GradientScaffold(
      appBar: const RoommeetAppBar(
        title: 'Shop Dashboard',
      ),
      drawer: const AppDrawer(),
      child: dashAsync.when(
        loading: () => const Padding(
          padding: EdgeInsets.fromLTRB(16, kToolbarHeight + 24, 16, 0),
          child: ShimmerStatGrid(),
        ),
        error: (e, _) => ErrorState(
          message: e.toString(),
          onRetry: () => ref.invalidate(shopDashboardProvider),
        ),
        data: (data) => _buildDash(context, data),
      ),
    );
  }

  Widget _buildDash(BuildContext context, Map<String, dynamic> data) {
    final shop = data['shop'] as Map<String, dynamic>? ?? {};
    final stats = data['stats'] as Map<String, dynamic>? ?? {};
    final verification = shop['verification_status'] as String? ?? 'Pending';

    return RefreshIndicator(
      color: AppTheme.accent,
      onRefresh: () async {},
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, kToolbarHeight + 24, 16, 100),
        children: [
          // Bento Stat Tiles
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 1.25,
            children: [
              StatTile(
                label: 'Pending Orders',
                value: '${stats['pending_orders'] ?? 0}',
                icon: Icons.pending_actions_rounded,
                color: AppTheme.warning,
                onTap: () => context.go('/shop/orders?status=Pending'),
              ),
              StatTile(
                label: 'Confirmed Orders',
                value: '${stats['confirmed_orders'] ?? 0}',
                icon: Icons.check_circle_rounded,
                color: AppTheme.success,
                onTap: () => context.go('/shop/orders?status=Confirmed'),
              ),
              StatTile(
                label: 'Medicines Listed',
                value: '${stats['total_medicines'] ?? 0}',
                icon: Icons.medical_services_rounded,
                color: AppTheme.accent,
                onTap: () => context.go('/shop/inventory'),
              ),
              StatTile(
                label: 'Store Rating',
                value: '${shop['rating_avg'] ?? 0.0}',
                icon: Icons.star_rounded,
                color: Colors.amber,
              ),
            ],
          ),
          const SizedBox(height: 20),

          // Pharmacy Details
          const Text('Store Information',
              style: TextStyle(color: AppTheme.textPrimary, fontSize: 16, fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      shop['name'] ?? 'Medical Shop',
                      style: const TextStyle(color: AppTheme.textPrimary, fontSize: 18, fontWeight: FontWeight.w700),
                    ),
                    StatusBadge(verification),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    const Icon(Icons.location_on_outlined, color: AppTheme.textSecondary, size: 16),
                    const SizedBox(width: 8),
                    Text(shop['location'] ?? 'Campus Store', style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
                  ],
                ),
                const SizedBox(height: 14),
                const Divider(color: AppTheme.divider, height: 1),
                const SizedBox(height: 14),
                const Text(
                  'SuperAdmin Verification',
                  style: TextStyle(color: AppTheme.textPrimary, fontSize: 14, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Your store profile and drug license are pending global verification. You can list products but residents will only discover approved shops.',
                  style: TextStyle(color: AppTheme.textSecondary, fontSize: 12, height: 1.5),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
