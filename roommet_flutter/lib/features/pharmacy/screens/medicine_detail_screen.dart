import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:roommet_flutter/core/config/app_config.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/features/pharmacy/providers/cart_provider.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

final medicineDetailProvider = FutureProvider.autoDispose.family<Map<String, dynamic>, int>((ref, id) async {
  return ApiService().getMedicineDetail(id);
});

class MedicineDetailScreen extends ConsumerWidget {
  final int medicineId;
  const MedicineDetailScreen({super.key, required this.medicineId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detailAsync = ref.watch(medicineDetailProvider(medicineId));

    return GradientScaffold(
      appBar: RoommeetAppBar(title: 'Medicine Details', showBack: true),
      child: detailAsync.when(
        loading: () => const ShimmerList(count: 3, itemHeight: 180),
        error: (e, _) => ErrorState(
          message: 'Failed to load details.',
          onRetry: () => ref.invalidate(medicineDetailProvider(medicineId)),
        ),
        data: (m) => _buildDetail(context, ref, m),
      ),
    );
  }

  Widget _buildDetail(BuildContext context, WidgetRef ref, Map<String, dynamic> m) {
    final price = m['price'] ?? 0.0;
    final photoUrl = m['photo_url'] as String?;
    final fullUrl = AppConfig.fullAssetUrl(photoUrl);

    final reviews = m['reviews'] as List? ?? [];
    final delivery = m['delivery_options'] as List? ?? ['Standard'];
    final payments = m['payment_options'] as List? ?? ['UPI', 'COD'];

    return Column(
      children: [
        Expanded(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, kToolbarHeight + 24, 16, 24),
            children: [
              // Hero Product Card
              GlassCard(
                padding: EdgeInsets.zero,
                child: Column(
                  children: [
                    Container(
                      height: 200,
                      width: double.infinity,
                      decoration: const BoxDecoration(
                        color: AppTheme.bgSurface,
                        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
                      ),
                      child: ClipRRect(
                        borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
                        child: Image.network(
                          fullUrl,
                          fit: BoxFit.contain,
                          errorBuilder: (_, __, ___) => const Center(
                            child: Icon(Icons.medical_services_outlined, color: AppTheme.textMuted, size: 64),
                          ),
                        ),
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  m['name'] ?? '',
                                  style: const TextStyle(color: AppTheme.textPrimary, fontSize: 20, fontWeight: FontWeight.w700),
                                ),
                              ),
                              Text(
                                '₹$price',
                                style: const TextStyle(color: AppTheme.success, fontSize: 22, fontWeight: FontWeight.w700),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Row(
                            children: [
                              Text(
                                m['category'] ?? 'General',
                                style: const TextStyle(color: AppTheme.accent, fontSize: 13, fontWeight: FontWeight.w600),
                              ),
                              const Spacer(),
                              const Icon(Icons.star_rounded, color: Colors.amber, size: 16),
                              const SizedBox(width: 4),
                              Text('${m['average_rating'] ?? 0.0}',
                                  style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13, fontWeight: FontWeight.w600)),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Description & Composition
              GlassCard(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Composition', style: TextStyle(color: AppTheme.textPrimary, fontSize: 15, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 6),
                    Text(m['salt_composition'] ?? 'Information unavailable.', style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
                    const SizedBox(height: 14),
                    const Text('Description', style: TextStyle(color: AppTheme.textPrimary, fontSize: 15, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 6),
                    Text(m['description'] ?? 'No description provided.', style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13, height: 1.5)),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Delivery Options
              GlassCard(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Delivery & Payment', style: TextStyle(color: AppTheme.textPrimary, fontSize: 15, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        const Icon(Icons.local_shipping_rounded, color: AppTheme.textSecondary, size: 16),
                        const SizedBox(width: 8),
                        Text('Delivery: ${delivery.join(", ")}', style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Icon(Icons.payment_rounded, color: AppTheme.textSecondary, size: 16),
                        const SizedBox(width: 8),
                        Text('Payments: ${payments.join(", ")}', style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Reviews
              GlassCard(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Customer Reviews', style: TextStyle(color: AppTheme.textPrimary, fontSize: 15, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 12),
                    if (reviews.isEmpty)
                      const Text('No reviews yet. Be the first to buy and review!', style: TextStyle(color: AppTheme.textMuted, fontSize: 12))
                    else
                      ...reviews.map((rev) {
                        final r = rev as Map<String, dynamic>;
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 10),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Text(r['reviewer'] ?? 'Anonymous', style: const TextStyle(color: AppTheme.textPrimary, fontSize: 12, fontWeight: FontWeight.w600)),
                                  const Spacer(),
                                  Row(
                                    children: List.generate(5, (idx) {
                                      final score = r['rating'] ?? 5;
                                      return Icon(Icons.star_rounded, color: idx < score ? Colors.amber : AppTheme.textMuted, size: 12);
                                    }),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 4),
                              Text(r['comment'] ?? '', style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                              const SizedBox(height: 4),
                              const Divider(color: AppTheme.divider, height: 1),
                            ],
                          ),
                        );
                      }),
                  ],
                ),
              ),
            ],
          ),
        ),
        // Add to Cart / Buy Button Bar
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: AppTheme.bgCard,
            border: Border(top: BorderSide(color: AppTheme.divider)),
          ),
          child: Row(
            children: [
              Expanded(
                child: PrimaryButton(
                  label: 'Add to Cart',
                  icon: Icons.add_shopping_cart_rounded,
                  onPressed: () {
                    ref.read(cartProvider.notifier).addToCart(m);
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('${m['name']} added to cart!')),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
