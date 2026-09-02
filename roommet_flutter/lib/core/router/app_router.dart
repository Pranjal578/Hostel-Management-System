import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:roommet_flutter/core/storage/token_storage.dart';
import 'package:roommet_flutter/features/auth/screens/home_screen.dart';
import 'package:roommet_flutter/features/auth/screens/login_screen.dart';
import 'package:roommet_flutter/features/auth/screens/otp_screen.dart';
import 'package:roommet_flutter/features/resident/screens/resident_shell.dart';
import 'package:roommet_flutter/features/resident/screens/resident_dashboard.dart';
import 'package:roommet_flutter/features/resident/screens/resident_payments_screen.dart';
import 'package:roommet_flutter/features/resident/screens/resident_notices_screen.dart';
import 'package:roommet_flutter/features/resident/screens/resident_chat_screen.dart';
import 'package:roommet_flutter/features/resident/screens/resident_qr_screen.dart';
import 'package:roommet_flutter/features/owner/screens/owner_shell.dart';
import 'package:roommet_flutter/features/owner/screens/owner_dashboard.dart';
import 'package:roommet_flutter/features/owner/screens/owner_residents_screen.dart';
import 'package:roommet_flutter/features/owner/screens/owner_payments_screen.dart';
import 'package:roommet_flutter/features/owner/screens/owner_notices_screen.dart';
import 'package:roommet_flutter/features/owner/screens/owner_chat_screen.dart';
import 'package:roommet_flutter/features/owner/screens/qr_scanner_screen.dart';
import 'package:roommet_flutter/features/admin/screens/admin_shell.dart';
import 'package:roommet_flutter/features/admin/screens/admin_dashboard.dart';
import 'package:roommet_flutter/features/admin/screens/admin_owners_screen.dart';
import 'package:roommet_flutter/features/admin/screens/admin_residents_screen.dart';
import 'package:roommet_flutter/features/admin/screens/admin_shops_screen.dart';
import 'package:roommet_flutter/features/pharmacy/screens/pharmacy_shell.dart';
import 'package:roommet_flutter/features/pharmacy/screens/pharmacy_marketplace.dart';
import 'package:roommet_flutter/features/pharmacy/screens/medicine_detail_screen.dart';
import 'package:roommet_flutter/features/pharmacy/screens/cart_screen.dart';
import 'package:roommet_flutter/features/pharmacy/screens/my_orders_screen.dart';
import 'package:roommet_flutter/features/shop_owner/screens/shop_shell.dart';
import 'package:roommet_flutter/features/shop_owner/screens/shop_dashboard.dart';
import 'package:roommet_flutter/features/shop_owner/screens/shop_orders_screen.dart';
import 'package:roommet_flutter/features/shop_owner/screens/shop_inventory_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) async {
      final isAuth = await TokenStorage.isAuthenticated();
      final onAuth = state.matchedLocation == '/login' ||
          state.matchedLocation == '/otp' ||
          state.matchedLocation == '/';
      if (!isAuth && !onAuth) return '/login';
      if (isAuth && onAuth) {
        final role = await TokenStorage.getRole();
        return _homeForRole(role);
      }
      return null;
    },
    routes: [
      // ── Welcome / Discovery / Home ────────────────────
      GoRoute(path: '/', builder: (_, __) => const HomeScreen()),

      // ── Auth ──────────────────────────────────────────
      GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
      GoRoute(
        path: '/otp',
        builder: (_, state) => OtpScreen(email: state.extra as String? ?? ''),
      ),

      // ── Resident Shell ─────────────────────────────────
      ShellRoute(
        builder: (_, __, child) => ResidentShell(child: child),
        routes: [
          GoRoute(path: '/resident', builder: (_, __) => const ResidentDashboard()),
          GoRoute(path: '/resident/payments', builder: (_, __) => const ResidentPaymentsScreen()),
          GoRoute(path: '/resident/notices', builder: (_, __) => const ResidentNoticesScreen()),
          GoRoute(path: '/resident/chat', builder: (_, __) => const ResidentChatScreen()),
          GoRoute(path: '/resident/qr', builder: (_, __) => const ResidentQrScreen()),
        ],
      ),

      // ── Owner Shell ────────────────────────────────────
      ShellRoute(
        builder: (_, __, child) => OwnerShell(child: child),
        routes: [
          GoRoute(path: '/owner', builder: (_, __) => const OwnerDashboard()),
          GoRoute(path: '/owner/residents', builder: (_, __) => const OwnerResidentsScreen()),
          GoRoute(path: '/owner/payments', builder: (_, __) => const OwnerPaymentsScreen()),
          GoRoute(path: '/owner/notices', builder: (_, __) => const OwnerNoticesScreen()),
          GoRoute(path: '/owner/chat', builder: (_, __) => const OwnerChatScreen()),
          GoRoute(path: '/owner/scan', builder: (_, __) => const QrScannerScreen()),
        ],
      ),

      // ── Admin Shell ────────────────────────────────────
      ShellRoute(
        builder: (_, __, child) => AdminShell(child: child),
        routes: [
          GoRoute(path: '/admin', builder: (_, __) => const AdminDashboard()),
          GoRoute(path: '/admin/owners', builder: (_, __) => const AdminOwnersScreen()),
          GoRoute(path: '/admin/residents', builder: (_, __) => const AdminResidentsScreen()),
          GoRoute(path: '/admin/shops', builder: (_, __) => const AdminShopsScreen()),
        ],
      ),

      // ── Pharmacy Shell (accessible to Resident & ShopOwner) ──
      ShellRoute(
        builder: (_, __, child) => PharmacyShell(child: child),
        routes: [
          GoRoute(path: '/pharmacy', builder: (_, __) => const PharmacyMarketplace()),
          GoRoute(
            path: '/pharmacy/medicine/:id',
            builder: (_, state) => MedicineDetailScreen(
              medicineId: int.parse(state.pathParameters['id']!),
            ),
          ),
          GoRoute(path: '/pharmacy/cart', builder: (_, __) => const CartScreen()),
          GoRoute(path: '/pharmacy/orders', builder: (_, __) => const MyOrdersScreen()),
        ],
      ),

      // ── Shop Owner Shell ───────────────────────────────
      ShellRoute(
        builder: (_, __, child) => ShopShell(child: child),
        routes: [
          GoRoute(path: '/shop', builder: (_, __) => const ShopDashboard()),
          GoRoute(path: '/shop/orders', builder: (_, __) => const ShopOrdersScreen()),
          GoRoute(path: '/shop/inventory', builder: (_, __) => const ShopInventoryScreen()),
        ],
      ),
    ],
  );
});

String _homeForRole(String? role) {
  switch (role) {
    case 'Resident':    return '/resident';
    case 'HostelOwner': return '/owner';
    case 'SuperAdmin':  return '/admin';
    case 'ShopOwner':   return '/shop';
    default:            return '/login';
  }
}
