import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';

class PharmacyShell extends StatelessWidget {
  final Widget child;
  const PharmacyShell({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    final currentIndex = _indexFor(location);

    return Scaffold(
      body: child,
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: AppTheme.bgCard,
          border: Border(top: BorderSide(color: AppTheme.divider)),
        ),
        child: BottomNavigationBar(
          currentIndex: currentIndex,
          onTap: (i) {
            if (i == 3) {
              // Back to Main App Dashboard
              context.go('/resident'); // or owner depending on user role, go to '/resident' by default
            } else {
              context.go(_routeFor(i));
            }
          },
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.storefront_rounded), label: 'Shop'),
            BottomNavigationBarItem(icon: Icon(Icons.shopping_cart_rounded), label: 'Cart'),
            BottomNavigationBarItem(icon: Icon(Icons.receipt_long_rounded), label: 'My Orders'),
            BottomNavigationBarItem(icon: Icon(Icons.exit_to_app_rounded), label: 'Exit Shop'),
          ],
        ),
      ),
    );
  }

  int _indexFor(String loc) {
    if (loc.startsWith('/pharmacy/cart')) return 1;
    if (loc.startsWith('/pharmacy/orders')) return 2;
    return 0;
  }

  String _routeFor(int i) {
    switch (i) {
      case 1: return '/pharmacy/cart';
      case 2: return '/pharmacy/orders';
      default: return '/pharmacy';
    }
  }
}
