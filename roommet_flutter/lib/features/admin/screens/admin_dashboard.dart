import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/features/auth/providers/auth_provider.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

import 'package:roommet_flutter/shared/widgets/app_drawer.dart';

final adminStatsProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  return ApiService().getAdminStats();
});

class AdminDashboard extends ConsumerWidget {
  const AdminDashboard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final statsAsync = ref.watch(adminStatsProvider);

    return GradientScaffold(
      appBar: const RoommeetAppBar(
        title: 'Super Admin',
      ),
      drawer: const AppDrawer(),
      child: statsAsync.when(
        loading: () => const Padding(
          padding: EdgeInsets.fromLTRB(16, kToolbarHeight + 24, 16, 0),
          child: ShimmerStatGrid(),
        ),
        error: (e, _) => ErrorState(
          message: e.toString(),
          onRetry: () => ref.invalidate(adminStatsProvider),
        ),
        data: (stats) => _buildDashboard(context, stats),
      ),
    );
  }

  Widget _buildDashboard(BuildContext context, Map<String, dynamic> stats) {
    final residents = stats['residents'] as Map<String, dynamic>? ?? {};
    final payments  = stats['payments']  as Map<String, dynamic>? ?? {};
    final shops     = stats['shops']     as Map<String, dynamic>? ?? {};
    final active    = residents['active']  as int? ?? 0;
    final pending   = residents['pending'] as int? ?? 0;
    final total     = residents['total']   as int? ?? 1;

    return RefreshIndicator(
      color: AppTheme.accent,
      onRefresh: () async {},
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, kToolbarHeight + 24, 16, 100),
        children: [
          // ── Stats Grid ──────────────────────────
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 1.2,
            children: [
              StatTile(label: 'Total Residents', value: '${residents['total'] ?? 0}', icon: Icons.people_rounded, color: AppTheme.accent, onTap: () => context.go('/admin/residents')),
              StatTile(label: 'Hostel Owners', value: '${stats['hostels'] ?? 0}', icon: Icons.home_work_rounded, color: AppTheme.info, onTap: () => context.go('/admin/owners')),
              StatTile(label: 'Pending Payments', value: '${payments['pending'] ?? 0}', icon: Icons.receipt_rounded, color: AppTheme.warning),
              StatTile(label: 'Shops Pending', value: '${shops['pending'] ?? 0}', icon: Icons.store_rounded, color: AppTheme.danger, onTap: () => context.go('/admin/shops')),
            ],
          ),
          const SizedBox(height: 24),

          // ── Resident Status Chart ────────────────
          GlassCard(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Resident Status',
                    style: TextStyle(color: AppTheme.textPrimary, fontSize: 15, fontWeight: FontWeight.w600)),
                const SizedBox(height: 20),
                SizedBox(
                  height: 160,
                  child: PieChart(
                    PieChartData(
                      sectionsSpace: 3,
                      centerSpaceRadius: 40,
                      sections: [
                        PieChartSectionData(
                          value: active.toDouble(),
                          color: AppTheme.success,
                          title: 'Active\n$active',
                          titleStyle: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600),
                          radius: 60,
                        ),
                        PieChartSectionData(
                          value: pending.toDouble(),
                          color: AppTheme.warning,
                          title: 'Pending\n$pending',
                          titleStyle: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600),
                          radius: 60,
                        ),
                        PieChartSectionData(
                          value: (total - active - pending).toDouble().clamp(0, double.infinity),
                          color: AppTheme.danger,
                          title: 'Other',
                          titleStyle: const TextStyle(color: Colors.white, fontSize: 11),
                          radius: 60,
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // ── Payment & Orders stats ───────────────
          Row(
            children: [
              Expanded(
                child: GlassCard(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      const Icon(Icons.receipt_long_rounded, color: AppTheme.warning, size: 28),
                      const SizedBox(height: 8),
                      Text('${payments['total'] ?? 0}',
                          style: const TextStyle(color: AppTheme.textPrimary, fontSize: 22, fontWeight: FontWeight.w700)),
                      const Text('Total Payments', style: TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: GlassCard(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      const Icon(Icons.shopping_bag_rounded, color: AppTheme.success, size: 28),
                      const SizedBox(height: 8),
                      Text('${stats['orders'] ?? 0}',
                          style: const TextStyle(color: AppTheme.textPrimary, fontSize: 22, fontWeight: FontWeight.w700)),
                      const Text('Total Orders', style: TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
