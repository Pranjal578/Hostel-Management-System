import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/features/pharmacy/providers/cart_provider.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';

class CartScreen extends ConsumerStatefulWidget {
  const CartScreen({super.key});

  @override
  ConsumerState<CartScreen> createState() => _CartScreenState();
}

class _CartScreenState extends ConsumerState<CartScreen> {
  final _addressCtrl = TextEditingController();
  final _phoneCtrl    = TextEditingController();
  final _notesCtrl    = TextEditingController();
  String _deliveryOption = 'Standard';
  String _paymentOption  = 'COD';
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _addressCtrl.dispose();
    _phoneCtrl.dispose();
    _notesCtrl.dispose();
    super.dispose();
  }

  Future<void> _checkout() async {
    final cart = ref.read(cartProvider);
    if (cart.isEmpty) return;

    if (_addressCtrl.text.isEmpty || _phoneCtrl.text.isEmpty) {
      setState(() => _error = 'Delivery address and phone number are required.');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      // Loop through cart items and place order for each
      for (final item in cart) {
        await ApiService().placeOrder({
          'medicine_id': item.id,
          'quantity': item.quantity,
          'delivery_option': _deliveryOption,
          'payment_option': _paymentOption,
          'delivery_address': _addressCtrl.text.trim(),
          'contact_phone': _phoneCtrl.text.trim(),
          'notes': _notesCtrl.text.trim(),
        });
      }

      ref.read(cartProvider.notifier).clear();
      setState(() => _loading = false);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Orders placed successfully!')),
        );
        context.go('/pharmacy/orders');
      }
    } catch (e) {
      setState(() {
        _loading = false;
        _error = 'Checkout failed: $e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final cart = ref.watch(cartProvider);

    return GradientScaffold(
      appBar: RoommeetAppBar(title: 'Your Cart', showBack: true),
      child: cart.isEmpty
          ? const EmptyState(
              icon: Icons.shopping_cart_outlined,
              title: 'Cart is Empty',
              subtitle: 'Browse the medical store to add items to your cart.',
            )
          : Column(
              children: [
                Expanded(
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(16, kToolbarHeight + 24, 16, 24),
                    children: [
                      // Cart Items List
                      const Text('Selected Items',
                          style: TextStyle(color: AppTheme.textPrimary, fontSize: 16, fontWeight: FontWeight.w600)),
                      const SizedBox(height: 12),
                      ...cart.map((item) => _CartItemTile(item: item)),
                      const SizedBox(height: 20),

                      // Delivery Details Form
                      const Text('Delivery Information',
                          style: TextStyle(color: AppTheme.textPrimary, fontSize: 16, fontWeight: FontWeight.w600)),
                      const SizedBox(height: 12),
                      GlassCard(
                        child: Column(
                          children: [
                            TextField(
                              controller: _addressCtrl,
                              style: const TextStyle(color: AppTheme.textPrimary),
                              decoration: const InputDecoration(
                                labelText: 'Delivery Address (Hostel / Room No.)',
                                prefixIcon: Icon(Icons.location_on_outlined, color: AppTheme.textSecondary),
                              ),
                            ),
                            const SizedBox(height: 12),
                            TextField(
                              controller: _phoneCtrl,
                              keyboardType: TextInputType.phone,
                              style: const TextStyle(color: AppTheme.textPrimary),
                              decoration: const InputDecoration(
                                labelText: 'Contact Phone Number',
                                prefixIcon: Icon(Icons.phone_outlined, color: AppTheme.textSecondary),
                              ),
                            ),
                            const SizedBox(height: 12),
                            TextField(
                              controller: _notesCtrl,
                              style: const TextStyle(color: AppTheme.textPrimary),
                              decoration: const InputDecoration(
                                labelText: 'Special Instructions / Notes',
                                prefixIcon: Icon(Icons.note_alt_outlined, color: AppTheme.textSecondary),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 20),

                      // Delivery & Payment Settings
                      const Text('Settings',
                          style: TextStyle(color: AppTheme.textPrimary, fontSize: 16, fontWeight: FontWeight.w600)),
                      const SizedBox(height: 12),
                      GlassCard(
                        child: Column(
                          children: [
                            DropdownButtonFormField<String>(
                              value: _deliveryOption,
                              dropdownColor: AppTheme.bgCard,
                              style: const TextStyle(color: AppTheme.textPrimary),
                              decoration: const InputDecoration(labelText: 'Delivery Option'),
                              items: const [
                                DropdownMenuItem(value: 'Standard', child: Text('Standard (Free)')),
                                DropdownMenuItem(value: 'Express', child: Text('Express (Fast)')),
                              ],
                              onChanged: (v) => setState(() => _deliveryOption = v ?? 'Standard'),
                            ),
                            const SizedBox(height: 12),
                            DropdownButtonFormField<String>(
                              value: _paymentOption,
                              dropdownColor: AppTheme.bgCard,
                              style: const TextStyle(color: AppTheme.textPrimary),
                              decoration: const InputDecoration(labelText: 'Payment Method'),
                              items: const [
                                DropdownMenuItem(value: 'COD', child: Text('Cash on Delivery (COD)')),
                                DropdownMenuItem(value: 'UPI', child: Text('UPI on Delivery')),
                              ],
                              onChanged: (v) => setState(() => _paymentOption = v ?? 'COD'),
                            ),
                          ],
                        ),
                      ),
                      if (_error != null) ...[
                        const SizedBox(height: 16),
                        Text(_error!, style: const TextStyle(color: AppTheme.danger, fontSize: 13)),
                      ],
                    ],
                  ),
                ),
                // Checkout Bar
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: AppTheme.bgCard,
                    border: Border(top: BorderSide(color: AppTheme.divider)),
                  ),
                  child: Row(
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Text('Total Price', style: TextStyle(color: AppTheme.textMuted, fontSize: 12)),
                          Text(
                            '₹${ref.read(cartProvider.notifier).totalPrice.toStringAsFixed(2)}',
                            style: const TextStyle(color: AppTheme.success, fontSize: 20, fontWeight: FontWeight.w700),
                          ),
                        ],
                      ),
                      const SizedBox(width: 24),
                      Expanded(
                        child: PrimaryButton(
                          label: 'Checkout',
                          icon: Icons.shopping_bag_rounded,
                          onPressed: _checkout,
                          isLoading: _loading,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}

class _CartItemTile extends ConsumerWidget {
  final CartItem item;
  const _CartItemTile({required this.item});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return GlassCard(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.name, style: const TextStyle(color: AppTheme.textPrimary, fontSize: 15, fontWeight: FontWeight.w600)),
                Text(item.shopName, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                const SizedBox(height: 4),
                Text('₹${item.price} each', style: const TextStyle(color: AppTheme.success, fontSize: 13, fontWeight: FontWeight.w500)),
              ],
            ),
          ),
          Row(
            children: [
              IconButton(
                icon: const Icon(Icons.remove_circle_outline, color: AppTheme.textSecondary),
                onPressed: () {
                  ref.read(cartProvider.notifier).updateQuantity(item.id, item.quantity - 1);
                },
              ),
              Text('${item.quantity}', style: const TextStyle(color: AppTheme.textPrimary, fontSize: 15, fontWeight: FontWeight.w700)),
              IconButton(
                icon: const Icon(Icons.add_circle_outline, color: AppTheme.textSecondary),
                onPressed: () {
                  ref.read(cartProvider.notifier).updateQuantity(item.id, item.quantity + 1);
                },
              ),
            ],
          ),
        ],
      ),
    );
  }
}
