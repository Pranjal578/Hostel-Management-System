import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/features/auth/providers/auth_provider.dart';

class AppDrawer extends ConsumerWidget {
  const AppDrawer({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    final isAuthenticated = auth.status == AuthStatus.authenticated;
    final role = auth.role;

    return Drawer(
      backgroundColor: AppTheme.bgCard,
      child: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFF1E163C), Color(0xFF0E0B1F)],
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── Header ────────────────────────────────────
            DrawerHeader(
              decoration: BoxDecoration(
                border: Border(bottom: BorderSide(color: AppTheme.divider, width: 1.5)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Row(
                    children: [
                      Container(
                        height: 48,
                        width: 48,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppTheme.accent, width: 1.5),
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(10),
                          child: Image.asset(
                            'assets/images/logo.jpg',
                            fit: BoxFit.cover,
                            errorBuilder: (_, __, ___) => const Icon(
                              Icons.home_work_rounded,
                              color: AppTheme.accent,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      const Text(
                        'ROOMMET',
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.textPrimary,
                          letterSpacing: 1.2,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  if (isAuthenticated) ...[
                    Text(
                      auth.email ?? 'Logged In User',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      role ?? '',
                      style: const TextStyle(
                        fontSize: 11,
                        color: AppTheme.accentGlow,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ] else ...[
                    const Text(
                      'Welcome, Guest',
                      style: TextStyle(
                        fontSize: 13,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                  ],
                ],
              ),
            ),

            // ── Menu Options ──────────────────────────────
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(vertical: 8),
                children: [
                  if (!isAuthenticated) ...[
                    // Public Menus
                    _DrawerTile(
                      icon: Icons.home_rounded,
                      title: 'Welcome Home',
                      onTap: () {
                        context.pop();
                        context.go('/');
                      },
                    ),
                    _DrawerTile(
                      icon: Icons.vpn_key_rounded,
                      title: 'Access Portal',
                      onTap: () {
                        context.pop();
                        context.go('/login');
                      },
                    ),
                    _DrawerTile(
                      icon: Icons.person_add_rounded,
                      title: 'Register Resident',
                      onTap: () => _showRegisterInfo(context, 'Resident'),
                    ),
                    _DrawerTile(
                      icon: Icons.domain_add_rounded,
                      title: 'Register Hostel Owner',
                      onTap: () => _showRegisterInfo(context, 'Hostel Owner'),
                    ),
                    _DrawerTile(
                      icon: Icons.add_business_rounded,
                      title: 'Register Shop Owner',
                      onTap: () => _showRegisterInfo(context, 'Shop Owner'),
                    ),
                  ] else ...[
                    // Role-Specific Menus
                    if (role == 'Resident') ...[
                      _DrawerTile(
                        icon: Icons.dashboard_rounded,
                        title: 'Dashboard',
                        onTap: () {
                          context.pop();
                          context.go('/resident');
                        },
                      ),
                      _DrawerTile(
                        icon: Icons.notifications_rounded,
                        title: 'Notices',
                        onTap: () {
                          context.pop();
                          context.go('/resident/notices');
                        },
                      ),
                      _DrawerTile(
                        icon: Icons.receipt_long_rounded,
                        title: 'Payments',
                        onTap: () {
                          context.pop();
                          context.go('/resident/payments');
                        },
                      ),
                      _DrawerTile(
                        icon: Icons.chat_bubble_rounded,
                        title: 'Chat',
                        onTap: () {
                          context.pop();
                          context.go('/resident/chat');
                        },
                      ),
                      _DrawerTile(
                        icon: Icons.storefront_rounded,
                        title: 'Pharmacy Marketplace',
                        onTap: () {
                          context.pop();
                          context.go('/pharmacy');
                        },
                      ),
                      _DrawerTile(
                        icon: Icons.shopping_bag_rounded,
                        title: 'My Orders',
                        onTap: () {
                          context.pop();
                          context.go('/pharmacy/orders');
                        },
                      ),
                      _DrawerTile(
                        icon: Icons.qr_code_rounded,
                        title: 'My QR Code',
                        onTap: () {
                          context.pop();
                          context.go('/resident/qr');
                        },
                      ),
                    ] else if (role == 'HostelOwner') ...[
                      _DrawerTile(
                        icon: Icons.dashboard_rounded,
                        title: 'Owner Dashboard',
                        onTap: () {
                          context.pop();
                          context.go('/owner');
                        },
                      ),
                      _DrawerTile(
                        icon: Icons.people_rounded,
                        title: 'Residents',
                        onTap: () {
                          context.pop();
                          context.go('/owner/residents');
                        },
                      ),
                      _DrawerTile(
                        icon: Icons.receipt_rounded,
                        title: 'Payments Dues',
                        onTap: () {
                          context.pop();
                          context.go('/owner/payments');
                        },
                      ),
                      _DrawerTile(
                        icon: Icons.campaign_rounded,
                        title: 'Notice Board',
                        onTap: () {
                          context.pop();
                          context.go('/owner/notices');
                        },
                      ),
                      _DrawerTile(
                        icon: Icons.chat_bubble_rounded,
                        title: 'Support Chat',
                        onTap: () {
                          context.pop();
                          context.go('/owner/chat');
                        },
                      ),
                      _DrawerTile(
                        icon: Icons.storefront_rounded,
                        title: 'Pharmacy Marketplace',
                        onTap: () {
                          context.pop();
                          context.go('/pharmacy');
                        },
                      ),
                    ] else if (role == 'SuperAdmin') ...[
                      _DrawerTile(
                        icon: Icons.admin_panel_settings_rounded,
                        title: 'Admin Dashboard',
                        onTap: () {
                          context.pop();
                          context.go('/admin');
                        },
                      ),
                      _DrawerTile(
                        icon: Icons.manage_accounts_rounded,
                        title: 'Hostel Owners',
                        onTap: () {
                          context.pop();
                          context.go('/admin/owners');
                        },
                      ),
                      _DrawerTile(
                        icon: Icons.people_rounded,
                        title: 'Residents List',
                        onTap: () {
                          context.pop();
                          context.go('/admin/residents');
                        },
                      ),
                      _DrawerTile(
                        icon: Icons.storefront_rounded,
                        title: 'Shops Management',
                        onTap: () {
                          context.pop();
                          context.go('/admin/shops');
                        },
                      ),
                      _DrawerTile(
                        icon: Icons.local_pharmacy_rounded,
                        title: 'Pharmacy Marketplace',
                        onTap: () {
                          context.pop();
                          context.go('/pharmacy');
                        },
                      ),
                    ] else if (role == 'ShopOwner') ...[
                      _DrawerTile(
                        icon: Icons.dashboard_rounded,
                        title: 'Shop Dashboard',
                        onTap: () {
                          context.pop();
                          context.go('/shop');
                        },
                      ),
                      _DrawerTile(
                        icon: Icons.receipt_long_rounded,
                        title: 'Medicine Orders',
                        onTap: () {
                          context.pop();
                          context.go('/shop/orders');
                        },
                      ),
                      _DrawerTile(
                        icon: Icons.inventory_rounded,
                        title: 'Inventory list',
                        onTap: () {
                          context.pop();
                          context.go('/shop/inventory');
                        },
                      ),
                      _DrawerTile(
                        icon: Icons.storefront_rounded,
                        title: 'Marketplace View',
                        onTap: () {
                          context.pop();
                          context.go('/pharmacy');
                        },
                      ),
                    ],
                  ],
                ],
              ),
            ),

            // ── Footer ────────────────────────────────────
            if (isAuthenticated) ...[
              const Divider(color: Colors.white10, height: 1),
              Padding(
                padding: const EdgeInsets.all(16),
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.logout_rounded, color: AppTheme.danger, size: 18),
                  label: const Text('Logout', style: TextStyle(color: AppTheme.danger, fontWeight: FontWeight.bold)),
                  onPressed: () async {
                    context.pop();
                    await ref.read(authProvider.notifier).logout();
                    if (context.mounted) context.go('/');
                  },
                  style: OutlinedButton.styleFrom(
                    side: BorderSide(color: AppTheme.danger.withOpacity(0.3)),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _showRegisterInfo(BuildContext context, String userType) {
    context.pop();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.bgSurface,
        title: Text('Register as $userType', style: const TextStyle(color: AppTheme.textPrimary)),
        content: Text(
          'Registration for $userType is completed via our secure web interface.\n\n'
          'Please visit the web portal in your desktop/mobile browser to register your account, then log in here.',
          style: const TextStyle(color: AppTheme.textSecondary, height: 1.4),
        ),
        actions: [
          TextButton(
            onPressed: () => context.pop(),
            child: const Text('OK', style: TextStyle(color: AppTheme.accent)),
          ),
        ],
      ),
    );
  }
}

class _DrawerTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final VoidCallback onTap;

  const _DrawerTile({
    required this.icon,
    required this.title,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: AppTheme.textSecondary, size: 20),
      title: Text(
        title,
        style: const TextStyle(
          color: AppTheme.textPrimary,
          fontSize: 14,
          fontWeight: FontWeight.w500,
        ),
      ),
      onTap: onTap,
      dense: true,
      visualDensity: VisualDensity.compact,
    );
  }
}
