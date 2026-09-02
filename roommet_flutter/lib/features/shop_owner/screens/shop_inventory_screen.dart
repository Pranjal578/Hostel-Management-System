import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

final shopInventoryProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  return ApiService().getShopInventory();
});

class ShopInventoryScreen extends ConsumerWidget {
  const ShopInventoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final inventoryAsync = ref.watch(shopInventoryProvider);

    return GradientScaffold(
      appBar: RoommeetAppBar(
        title: 'Inventory Listings',
      ),
      child: inventoryAsync.when(
        loading: () => const ShimmerList(count: 5),
        error: (e, _) => ErrorState(
          message: 'Failed to load inventory.',
          onRetry: () => ref.invalidate(shopInventoryProvider),
        ),
        data: (medicines) {
          if (medicines.isEmpty) {
            return const EmptyState(
              icon: Icons.inventory_2_outlined,
              title: 'No Medicines Listed',
              subtitle: 'Add medicines in your store dashboard to start selling.',
            );
          }
          return RefreshIndicator(
            color: AppTheme.accent,
            onRefresh: () async => ref.invalidate(shopInventoryProvider),
            child: ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, kToolbarHeight + 24, 16, 24),
              itemCount: medicines.length,
              itemBuilder: (context, idx) {
                final m = medicines[idx] as Map<String, dynamic>;
                final available = m['is_available'] as bool? ?? false;

                return GlassCard(
                  margin: const EdgeInsets.only(bottom: 10),
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: AppTheme.accent.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.medical_services_rounded, color: AppTheme.accent, size: 24),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              m['name'] ?? '',
                              style: const TextStyle(color: AppTheme.textPrimary, fontSize: 15, fontWeight: FontWeight.w700),
                            ),
                            Text(
                              m['category'] ?? 'General',
                              style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Stock: ${m['stock_quantity'] ?? 0} left',
                              style: TextStyle(
                                color: (m['stock_quantity'] ?? 0) < 5 ? AppTheme.danger : AppTheme.textMuted,
                                fontSize: 11,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            '₹${m['price']}',
                            style: const TextStyle(color: AppTheme.success, fontSize: 16, fontWeight: FontWeight.w700),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            available ? 'In Stock' : 'Out of Stock',
                            style: TextStyle(
                              color: available ? AppTheme.success : AppTheme.danger,
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
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
