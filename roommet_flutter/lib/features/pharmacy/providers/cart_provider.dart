import 'package:flutter_riverpod/flutter_riverpod.dart';

class CartItem {
  final int id;
  final String name;
  final double price;
  final String photoUrl;
  final String shopName;
  final int shopId;
  int quantity;

  CartItem({
    required this.id,
    required this.name,
    required this.price,
    required this.photoUrl,
    required this.shopName,
    required this.shopId,
    this.quantity = 1,
  });

  CartItem copyWith({int? quantity}) {
    return CartItem(
      id: id,
      name: name,
      price: price,
      photoUrl: photoUrl,
      shopName: shopName,
      shopId: shopId,
      quantity: quantity ?? this.quantity,
    );
  }
}

class CartNotifier extends StateNotifier<List<CartItem>> {
  CartNotifier() : super([]);

  void addToCart(Map<String, dynamic> medicine) {
    final existingIndex = state.indexWhere((item) => item.id == medicine['id']);
    if (existingIndex != -1) {
      final updated = [...state];
      updated[existingIndex].quantity += 1;
      state = updated;
    } else {
      state = [
        ...state,
        CartItem(
          id: medicine['id'] as int,
          name: medicine['name'] as String? ?? '',
          price: (medicine['price'] as num?)?.toDouble() ?? 0.0,
          photoUrl: medicine['photo_url'] as String? ?? '',
          shopName: medicine['shop_name'] as String? ?? 'Pharmacy Store',
          shopId: medicine['shop_id'] as int,
        ),
      ];
    }
  }

  void updateQuantity(int medicineId, int qty) {
    if (qty <= 0) {
      removeFromCart(medicineId);
      return;
    }
    state = state.map((item) {
      if (item.id == medicineId) {
        return item.copyWith(quantity: qty);
      }
      return item;
    }).toList();
  }

  void removeFromCart(int medicineId) {
    state = state.where((item) => item.id != medicineId).toList();
  }

  void clear() {
    state = [];
  }

  double get totalPrice {
    return state.fold(0.0, (sum, item) => sum + (item.price * item.quantity));
  }
}

final cartProvider = StateNotifierProvider<CartNotifier, List<CartItem>>((ref) {
  return CartNotifier();
});
