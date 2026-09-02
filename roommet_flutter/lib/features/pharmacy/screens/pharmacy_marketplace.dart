import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:roommet_flutter/core/config/app_config.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/features/pharmacy/providers/cart_provider.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

import 'package:roommet_flutter/shared/widgets/app_drawer.dart';

final medicinesProvider = FutureProvider.autoDispose.family<Map<String, dynamic>, Map<String, dynamic>>((ref, params) async {
  return ApiService().getMedicines(
    page: params['page'] ?? 1,
    search: params['search'],
    category: params['category'],
  );
});

class PharmacyMarketplace extends ConsumerStatefulWidget {
  const PharmacyMarketplace({super.key});

  @override
  ConsumerState<PharmacyMarketplace> createState() => _PharmacyMarketplaceState();
}

class _PharmacyMarketplaceState extends ConsumerState<PharmacyMarketplace> {
  String _search = '';
  String _category = '';
  final _searchCtrl = TextEditingController();

  final List<String> _categories = [
    'All',
    'Analgesic',
    'Antibiotic',
    'Antiseptic',
    'Vitamins',
    'First Aid',
  ];

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final params = {
      'page': 1,
      'search': _search.isEmpty ? null : _search,
      'category': (_category == 'All' || _category.isEmpty) ? null : _category,
    };
    final medsAsync = ref.watch(medicinesProvider(params));

    return GradientScaffold(
      appBar: RoommeetAppBar(
        title: 'Medical Store',
        actions: [
          IconButton(
            icon: const Icon(Icons.shopping_cart_rounded, color: AppTheme.textSecondary),
            onPressed: () => context.go('/pharmacy/cart'),
          ),
        ],
      ),
      drawer: const AppDrawer(),
      child: Column(
        children: [
          SizedBox(height: kToolbarHeight + 16),
          // Search Bar
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: TextField(
              controller: _searchCtrl,
              style: const TextStyle(color: AppTheme.textPrimary, fontSize: 14),
              decoration: InputDecoration(
                hintText: 'Search by salt or medicine name...',
                prefixIcon: const Icon(Icons.search_rounded, color: AppTheme.textSecondary, size: 20),
                suffixIcon: _search.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.close_rounded, color: AppTheme.textSecondary, size: 18),
                        onPressed: () {
                          _searchCtrl.clear();
                          setState(() => _search = '');
                        },
                      )
                    : null,
              ),
              onChanged: (v) => setState(() => _search = v.trim()),
            ),
          ),
          const SizedBox(height: 12),
          // Category Selectors
          SizedBox(
            height: 38,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: _categories.length,
              itemBuilder: (context, i) {
                final cat = _categories[i];
                final isSelected = (_category.isEmpty && cat == 'All') || (_category == cat);
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ChoiceChip(
                    label: Text(cat),
                    selected: isSelected,
                    selectedColor: AppTheme.accent,
                    backgroundColor: AppTheme.bgCard,
                    labelStyle: TextStyle(
                      color: isSelected ? Colors.white : AppTheme.textSecondary,
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                    ),
                    onSelected: (selected) {
                      setState(() {
                        _category = cat == 'All' ? '' : cat;
                      });
                    },
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 12),
          // Medicines Grid
          Expanded(
            child: medsAsync.when(
              loading: () => GridView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  childAspectRatio: 0.75,
                ),
                itemCount: 6,
                itemBuilder: (_, __) => const MedicineSkeletonTile(),
              ),
              error: (e, _) => ErrorState(
                message: 'Error fetching products.',
                onRetry: () => ref.invalidate(medicinesProvider(params)),
              ),
              data: (data) {
                final medicines = data['medicines'] as List? ?? [];
                if (medicines.isEmpty) {
                  return const EmptyState(
                    icon: Icons.search_off_rounded,
                    title: 'No Medicines Found',
                    subtitle: 'Try searching for generic salts or active compounds.',
                  );
                }
                return RefreshIndicator(
                  color: AppTheme.accent,
                  onRefresh: () async => ref.invalidate(medicinesProvider(params)),
                  child: GridView.builder(
                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 100),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      crossAxisSpacing: 12,
                      mainAxisSpacing: 12,
                      childAspectRatio: 0.72,
                    ),
                    itemCount: medicines.length,
                    itemBuilder: (context, idx) {
                      final m = medicines[idx] as Map<String, dynamic>;
                      return _MedicineCard(medicine: m);
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _MedicineCard extends ConsumerWidget {
  final Map<String, dynamic> medicine;
  const _MedicineCard({required this.medicine});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final price = medicine['price'] ?? 0.0;
    final photoUrl = medicine['photo_url'] as String?;
    final fullUrl = AppConfig.fullAssetUrl(photoUrl);

    return GlassCard(
      padding: EdgeInsets.zero,
      onTap: () => context.go('/pharmacy/medicine/${medicine['id']}'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Image / Icon
          Expanded(
            child: Container(
              width: double.infinity,
              decoration: const BoxDecoration(
                color: AppTheme.bgSurface,
                borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
              ),
              child: ClipRRect(
                borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
                child: Image.network(
                  fullUrl,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => const Center(
                    child: Icon(Icons.medical_services_outlined, color: AppTheme.textMuted, size: 40),
                  ),
                ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  medicine['name'] ?? '',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: AppTheme.textPrimary, fontSize: 14, fontWeight: FontWeight.w600),
                ),
                Text(
                  medicine['salt_composition'] ?? 'Composition details',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: AppTheme.textSecondary, fontSize: 11),
                ),
                const SizedBox(height: 6),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '₹$price',
                      style: const TextStyle(color: AppTheme.success, fontSize: 15, fontWeight: FontWeight.w700),
                    ),
                    GestureDetector(
                      onTap: () {
                        ref.read(cartProvider.notifier).addToCart(medicine);
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text('${medicine['name']} added to cart!'),
                            duration: const Duration(seconds: 1),
                          ),
                        );
                      },
                      child: Container(
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(
                          gradient: AppTheme.accentGradient,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Icon(Icons.add_shopping_cart_rounded, color: Colors.white, size: 16),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
