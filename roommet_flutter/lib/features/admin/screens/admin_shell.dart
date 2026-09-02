import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';

class AdminShell extends StatelessWidget {
  final Widget child;
  const AdminShell({super.key, required this.child});
  @override
  Widget build(BuildContext context) {
    final loc = GoRouterState.of(context).matchedLocation;
    final idx = loc.startsWith('/admin/owners') ? 1 : loc.startsWith('/admin/residents') ? 2 : loc.startsWith('/admin/shops') ? 3 : 0;
    return Scaffold(
      body: child,
      bottomNavigationBar: Container(
        decoration: BoxDecoration(color: AppTheme.bgCard, border: Border(top: BorderSide(color: AppTheme.divider))),
        child: BottomNavigationBar(
          currentIndex: idx,
          onTap: (i) => context.go(['/admin', '/admin/owners', '/admin/residents', '/admin/shops'][i]),
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.bar_chart_rounded), label: 'Stats'),
            BottomNavigationBarItem(icon: Icon(Icons.person_rounded), label: 'Owners'),
            BottomNavigationBarItem(icon: Icon(Icons.people_rounded), label: 'Residents'),
            BottomNavigationBarItem(icon: Icon(Icons.store_rounded), label: 'Shops'),
          ],
        ),
      ),
    );
  }
}
