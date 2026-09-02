import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';

class ShopShell extends StatelessWidget {
  final Widget child;
  const ShopShell({super.key, required this.child});

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
          onTap: (i) => context.go(_routeFor(i)),
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.dashboard_rounded), label: 'Dashboard'),
            BottomNavigationBarItem(icon: Icon(Icons.shopping_bag_rounded), label: 'Orders'),
            BottomNavigationBarItem(icon: Icon(Icons.inventory_rounded), label: 'Inventory'),
          ],
        ),
      ),
    );
  }

  int _indexFor(String loc) {
    if (loc.startsWith('/shop/orders')) return 1;
    if (loc.startsWith('/shop/inventory')) return 2;
    return 0;
  }

  String _routeFor(int i) {
    switch (i) {
      case 1: return '/shop/orders';
      case 2: return '/shop/inventory';
      default: return '/shop';
    }
  }
}
