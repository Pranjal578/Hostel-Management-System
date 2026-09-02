import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/features/auth/providers/auth_provider.dart';

class ResidentShell extends ConsumerWidget {
  final Widget child;
  const ResidentShell({super.key, required this.child});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
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
            BottomNavigationBarItem(
                icon: Icon(Icons.dashboard_rounded), label: 'Home'),
            BottomNavigationBarItem(
                icon: Icon(Icons.receipt_long_rounded), label: 'Payments'),
            BottomNavigationBarItem(
                icon: Icon(Icons.qr_code_rounded), label: 'My QR'),
            BottomNavigationBarItem(
                icon: Icon(Icons.notifications_rounded), label: 'Notices'),
            BottomNavigationBarItem(
                icon: Icon(Icons.chat_bubble_rounded), label: 'Chat'),
          ],
        ),
      ),
    );
  }

  int _indexFor(String location) {
    if (location.startsWith('/resident/payments')) return 1;
    if (location.startsWith('/resident/qr'))       return 2;
    if (location.startsWith('/resident/notices'))  return 3;
    if (location.startsWith('/resident/chat'))     return 4;
    return 0;
  }

  String _routeFor(int i) {
    switch (i) {
      case 1: return '/resident/payments';
      case 2: return '/resident/qr';
      case 3: return '/resident/notices';
      case 4: return '/resident/chat';
      default: return '/resident';
    }
  }
}
