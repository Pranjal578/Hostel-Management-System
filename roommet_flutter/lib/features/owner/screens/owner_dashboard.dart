import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/features/auth/providers/auth_provider.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

import 'package:roommet_flutter/shared/widgets/app_drawer.dart';

final ownerDashboardProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  return ApiService().getOwnerDashboard();
});

class OwnerDashboard extends ConsumerWidget {
  const OwnerDashboard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashAsync = ref.watch(ownerDashboardProvider);

    return GradientScaffold(
      appBar: const RoommeetAppBar(
        title: 'Owner Dashboard',
      ),
      drawer: const AppDrawer(),
      child: dashAsync.when(
        loading: () => const Padding(
          padding: EdgeInsets.fromLTRB(16, kToolbarHeight + 24, 16, 0),
          child: ShimmerStatGrid(),
        ),
        error: (e, _) => ErrorState(
          message: e.toString(),
          onRetry: () => ref.invalidate(ownerDashboardProvider),
        ),
        data: (data) => _buildDash(context, data),
      ),
    );
  }

  Widget _buildDash(BuildContext context, Map<String, dynamic> data) {
    final hostels = data['hostels'] as List? ?? [];
    return RefreshIndicator(
      color: AppTheme.accent,
      onRefresh: () async {},
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, kToolbarHeight + 24, 16, 100),
        children: [
          // ── Stats Grid (Real Dynamic Metrics) ─────────────────────────────
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 1.25,
            children: [
              StatTile(
                label: 'Active Residents',
                value: '${data['active_residents'] ?? data['total_residents'] ?? 0}',
                icon: Icons.people_rounded,
                color: AppTheme.accent,
                onTap: () => context.go('/owner/residents'),
              ),
              StatTile(
                label: 'Rent Reconciled',
                value: '₹${(data['total_rent_collected'] as num? ?? 0).toStringAsFixed(0)}',
                icon: Icons.payments_rounded,
                color: AppTheme.success,
                onTap: () => context.go('/owner/payments'),
              ),
              StatTile(
                label: 'Pending Payments',
                value: '${data['pending_payments'] ?? 0}',
                icon: Icons.receipt_long_rounded,
                color: AppTheme.warning,
                onTap: () => context.go('/owner/payments'),
              ),
              StatTile(
                label: 'Beds Allocated',
                value: '${data['occupied_rooms'] ?? 0} / ${data['total_capacity'] ?? 0}',
                icon: Icons.bed_rounded,
                color: AppTheme.info,
              ),
              StatTile(
                label: 'Pending Approvals',
                value: '${data['pending_approvals'] ?? 0}',
                icon: Icons.person_add_rounded,
                color: AppTheme.danger,
                onTap: () => context.go('/owner/residents?status=Pending'),
              ),
              StatTile(
                label: 'Hostels Managed',
                value: '${data['hostel_count'] ?? 0}',
                icon: Icons.home_work_rounded,
                color: AppTheme.accentGlow,
              ),
            ],
          ),
          const SizedBox(height: 24),

          // ── Hostels ────────────────────────────────
          const Text('Your Hostels',
              style: TextStyle(
                  color: AppTheme.textPrimary,
                  fontSize: 16,
                  fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),
          ...hostels.map((h) => _HostelCard(h as Map<String, dynamic>)),

          const SizedBox(height: 20),
          // ── Quick scan banner ──────────────────────
          GlassCard(
            padding: const EdgeInsets.all(16),
            onTap: () => context.go('/owner/scan'),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    gradient: AppTheme.accentGradient,
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: const Icon(Icons.qr_code_scanner_rounded,
                      color: Colors.white, size: 24),
                ),
                const SizedBox(width: 14),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Scan Resident QR',
                          style: TextStyle(
                              color: AppTheme.textPrimary,
                              fontSize: 15,
                              fontWeight: FontWeight.w600)),
                      Text("Tap or use FAB to scan a resident's identity code",
                          style: TextStyle(
                              color: AppTheme.textSecondary, fontSize: 12)),
                    ],
                  ),
                ),
                const Icon(Icons.arrow_forward_ios_rounded,
                    color: AppTheme.textMuted, size: 14),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _HostelCard extends StatelessWidget {
  final Map<String, dynamic> hostel;
  const _HostelCard(this.hostel);

  @override
  Widget build(BuildContext context) {
    final available = hostel['available_rooms'] as int? ?? 0;
    final capacity = hostel['capacity'] as int? ?? 1;
    final occupancy = 1 - (available / capacity);

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
                child: const Icon(Icons.home_work_rounded,
                    color: AppTheme.accent, size: 18),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(hostel['name'] ?? '',
                        style: const TextStyle(
                            color: AppTheme.textPrimary,
                            fontSize: 15,
                            fontWeight: FontWeight.w600)),
                    Text(hostel['location'] ?? '',
                        style: const TextStyle(
                            color: AppTheme.textSecondary, fontSize: 12)),
                  ],
                ),
              ),
              StatusBadge(hostel['code'] ?? ''),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              _stat('Residents', '${hostel['resident_count'] ?? 0}'),
              _stat('Available', '$available'),
              _stat('Capacity', '$capacity'),
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: occupancy.clamp(0.0, 1.0),
              backgroundColor: AppTheme.bgSurface,
              valueColor: AlwaysStoppedAnimation(
                occupancy > 0.85 ? AppTheme.danger : AppTheme.accent,
              ),
              minHeight: 6,
            ),
          ),
          const SizedBox(height: 6),
          Text('${(occupancy * 100).toStringAsFixed(0)}% occupancy',
              style: const TextStyle(
                  color: AppTheme.textMuted, fontSize: 11)),
        ],
      ),
    );
  }

  Widget _stat(String label, String value) => Expanded(
        child: Column(
          children: [
            Text(value,
                style: const TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 16,
                    fontWeight: FontWeight.w700)),
            Text(label,
                style: const TextStyle(
                    color: AppTheme.textMuted, fontSize: 11)),
          ],
        ),
      );
}
