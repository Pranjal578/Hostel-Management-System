import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/features/auth/providers/auth_provider.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

import 'package:roommet_flutter/shared/widgets/app_drawer.dart';

final residentProfileProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  return ApiService().getResidentProfile();
});

class ResidentDashboard extends ConsumerWidget {
  const ResidentDashboard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profileAsync = ref.watch(residentProfileProvider);

    return GradientScaffold(
      appBar: const RoommeetAppBar(
        title: 'ROOMMET',
      ),
      drawer: const AppDrawer(),
      child: profileAsync.when(
        loading: () => const ShimmerList(count: 4, itemHeight: 120),
        error: (e, _) => ErrorState(
          message: e.toString().replaceAll('Exception:', '').trim(),
          onRetry: () => ref.invalidate(residentProfileProvider),
        ),
        data: (profile) => _buildDashboard(context, profile),
      ),
    );
  }

  Widget _buildDashboard(BuildContext context, Map<String, dynamic> profile) {
    final hostel = profile['hostel'] as Map<String, dynamic>?;
    final paymentStatus = profile['payment_status'] as String? ?? 'None';
    final status = profile['status'] as String? ?? 'Pending';

    return RefreshIndicator(
      color: AppTheme.accent,
      onRefresh: () async {},
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, kToolbarHeight + 24, 16, 100),
        children: [
          // ── Hero Profile Card ──────────────────────────
          AccentCard(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 30,
                  backgroundColor: Colors.white.withOpacity(0.2),
                  child: Text(
                    (profile['full_name'] as String? ?? '?')[0].toUpperCase(),
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 24,
                        fontWeight: FontWeight.w700),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        profile['full_name'] ?? 'Resident',
                        style: const TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        profile['email'] ?? '',
                        style: TextStyle(
                            color: Colors.white.withOpacity(0.8), fontSize: 13),
                      ),
                      const SizedBox(height: 6),
                      StatusBadge(status),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.qr_code_2_rounded,
                      color: Colors.white, size: 30),
                  onPressed: () => context.go('/resident/qr'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // ── Hostel Info ────────────────────────────────
          if (hostel != null) ...[
            GlassCard(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.home_work_rounded,
                          color: AppTheme.accent, size: 20),
                      const SizedBox(width: 8),
                      const Text('Your Hostel',
                          style: TextStyle(
                              color: AppTheme.textSecondary,
                              fontSize: 13,
                              fontWeight: FontWeight.w600)),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    hostel['name'] ?? '',
                    style: const TextStyle(
                        color: AppTheme.textPrimary,
                        fontSize: 18,
                        fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 4),
                  Text(hostel['location'] ?? '',
                      style: const TextStyle(
                          color: AppTheme.textSecondary, fontSize: 13)),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      _infoChip(Icons.meeting_room_rounded,
                          'Room ${profile['room_number'] ?? 'Pending'}'),
                      const SizedBox(width: 8),
                      _infoChip(Icons.tag_rounded, hostel['code'] ?? ''),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
          ],

          // ── Stats Grid ─────────────────────────────────
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 1.3,
            children: [
              StatTile(
                label: 'Rent Due',
                value: '₹${profile['rent'] ?? 0}',
                icon: Icons.currency_rupee_rounded,
                color: AppTheme.warning,
                onTap: () => context.go('/resident/payments'),
              ),
              StatTile(
                label: 'Payment Status',
                value: paymentStatus,
                icon: Icons.receipt_rounded,
                color: AppTheme.statusColor(paymentStatus),
                onTap: () => context.go('/resident/payments'),
              ),
              StatTile(
                label: 'Electricity',
                value: '₹${profile['electricity_bill'] ?? 0}',
                icon: Icons.bolt_rounded,
                color: AppTheme.info,
              ),
              StatTile(
                label: 'Profile',
                value: status,
                icon: Icons.verified_user_rounded,
                color: AppTheme.statusColor(status),
              ),
            ],
          ),
          const SizedBox(height: 20),

          // ── Quick Actions ─────────────────────────────
          const Text('Quick Actions',
              style: TextStyle(
                  color: AppTheme.textPrimary,
                  fontSize: 16,
                  fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _actionButton(
                  context,
                  icon: Icons.upload_rounded,
                  label: 'Pay Rent',
                  color: AppTheme.success,
                  route: '/resident/payments',
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _actionButton(
                  context,
                  icon: Icons.campaign_rounded,
                  label: 'Notices',
                  color: AppTheme.info,
                  route: '/resident/notices',
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _actionButton(
                  context,
                  icon: Icons.chat_rounded,
                  label: 'Chat',
                  color: AppTheme.accent,
                  route: '/resident/chat',
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),

          // ── Pharmacy Banner ───────────────────────────
          GestureDetector(
            onTap: () => context.go('/pharmacy'),
            child: AccentCard(
              gradient: const LinearGradient(
                colors: [Color(0xFF065F46), Color(0xFF047857)],
              ),
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  const Icon(Icons.medical_services_rounded,
                      color: Colors.white, size: 32),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Medical Store',
                            style: TextStyle(
                                color: Colors.white,
                                fontSize: 16,
                                fontWeight: FontWeight.w700)),
                        Text('Order medicines delivered to your room',
                            style: TextStyle(
                                color: Colors.white70, fontSize: 12)),
                      ],
                    ),
                  ),
                  const Icon(Icons.arrow_forward_ios_rounded,
                      color: Colors.white70, size: 16),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _infoChip(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: AppTheme.bgSurface,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: AppTheme.textSecondary),
          const SizedBox(width: 4),
          Text(label,
              style: const TextStyle(
                  color: AppTheme.textSecondary, fontSize: 12)),
        ],
      ),
    );
  }

  Widget _actionButton(BuildContext context,
      {required IconData icon,
      required String label,
      required Color color,
      required String route}) {
    return GestureDetector(
      onTap: () => context.go(route),
      child: GlassCard(
        padding: const EdgeInsets.symmetric(vertical: 16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: color.withOpacity(0.15),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: color, size: 22),
            ),
            const SizedBox(height: 8),
            Text(label,
                style: const TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: 12,
                    fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }
}
