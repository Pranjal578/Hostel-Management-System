import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';

class OwnerShell extends StatelessWidget {
  final Widget child;
  const OwnerShell({super.key, required this.child});

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
            BottomNavigationBarItem(icon: Icon(Icons.people_rounded), label: 'Residents'),
            BottomNavigationBarItem(icon: Icon(Icons.receipt_rounded), label: 'Payments'),
            BottomNavigationBarItem(icon: Icon(Icons.campaign_rounded), label: 'Notices'),
            BottomNavigationBarItem(icon: Icon(Icons.chat_bubble_rounded), label: 'Chat'),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.go('/owner/scan'),
        backgroundColor: AppTheme.accent,
        child: const Icon(Icons.qr_code_scanner_rounded, color: Colors.white),
      ),
    );
  }

  int _indexFor(String loc) {
    if (loc.startsWith('/owner/residents')) return 1;
    if (loc.startsWith('/owner/payments'))  return 2;
    if (loc.startsWith('/owner/notices'))   return 3;
    if (loc.startsWith('/owner/chat'))      return 4;
    return 0;
  }

  String _routeFor(int i) {
    switch (i) {
      case 1: return '/owner/residents';
      case 2: return '/owner/payments';
      case 3: return '/owner/notices';
      case 4: return '/owner/chat';
      default: return '/owner';
    }
  }
}
