import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

final myOrdersProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  return ApiService().getMyOrders();
});

class MyOrdersScreen extends ConsumerWidget {
  const MyOrdersScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ordersAsync = ref.watch(myOrdersProvider);

    return GradientScaffold(
      appBar: RoommeetAppBar(title: 'My Orders', showBack: true),
      child: ordersAsync.when(
        loading: () => const ShimmerList(count: 4, itemHeight: 140),
        error: (e, _) => ErrorState(
          message: 'Failed to load order history.',
          onRetry: () => ref.invalidate(myOrdersProvider),
        ),
        data: (data) {
          final orders = data['orders'] as List? ?? [];
          if (orders.isEmpty) {
            return const EmptyState(
              icon: Icons.receipt_long_rounded,
              title: 'No Orders Placed',
              subtitle: 'Place an order in the store to track delivery status.',
            );
          }
          return RefreshIndicator(
            color: AppTheme.accent,
            onRefresh: () async => ref.invalidate(myOrdersProvider),
            child: ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, kToolbarHeight + 24, 16, 24),
              itemCount: orders.length,
              itemBuilder: (context, i) {
                final o = orders[i] as Map<String, dynamic>;
                return _OrderTile(order: o);
              },
            ),
          );
        },
      ),
    );
  }
}

class _OrderTile extends StatelessWidget {
  final Map<String, dynamic> order;
  const _OrderTile({required this.order});

  @override
  Widget build(BuildContext context) {
    final status = order['status'] as String? ?? 'Pending';
    final deliveryStatus = order['delivery_status'] as String? ?? 'Order Placed';
    final stages = order['delivery_stages'] as List? ?? ['Order Placed', 'Confirmed', 'Packed', 'Out for Delivery', 'Delivered'];
    final stageIndex = order['delivery_stage_index'] as int? ?? 0;

    return GlassCard(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  order['medicine_name'] ?? 'Medicine Order',
                  style: const TextStyle(color: AppTheme.textPrimary, fontSize: 16, fontWeight: FontWeight.w700),
                ),
              ),
              StatusBadge(status),
            ],
          ),
          const SizedBox(height: 6),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Quantity: ${order['quantity']}',
                style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
              ),
              Text(
                '₹${order['total_price']}',
                style: const TextStyle(color: AppTheme.success, fontSize: 16, fontWeight: FontWeight.w700),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            'Placed on: ${order['created_at']}',
            style: const TextStyle(color: AppTheme.textMuted, fontSize: 11),
          ),
          const SizedBox(height: 14),
          const Divider(color: AppTheme.divider, height: 1),
          const SizedBox(height: 14),
          Text(
            'Delivery Stage: $deliveryStatus',
            style: const TextStyle(color: AppTheme.accent, fontSize: 13, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 10),
          // Progress Line
          Row(
            children: List.generate(stages.length, (idx) {
              final active = idx <= stageIndex;
              return Expanded(
                child: Container(
                  height: 4,
                  margin: EdgeInsets.only(right: idx == stages.length - 1 ? 0 : 4),
                  decoration: BoxDecoration(
                    color: active ? AppTheme.accent : AppTheme.divider,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              );
            }),
          ),
        ],
      ),
    );
  }
}
