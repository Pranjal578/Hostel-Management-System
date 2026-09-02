import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/shared/widgets/app_drawer.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  final _scrollController = ScrollController();
  final _discoveryKey = GlobalKey();
  List<dynamic>? _hostels;
  bool _loadingHostels = false;
  String? _hostelError;

  Future<void> _fetchPublicHostels() async {
    setState(() {
      _loadingHostels = true;
      _hostelError = null;
    });

    try {
      final data = await ApiService().getPublicHostels();
      setState(() {
        _hostels = data;
        _loadingHostels = false;
      });
    } catch (e) {
      setState(() {
        _hostelError = 'Could not fetch public hostels. Please check connection.';
        _loadingHostels = false;
      });
    }
  }

  void _scrollToDiscovery() {
    _fetchPublicHostels();
    Scrollable.ensureVisible(
      _discoveryKey.currentContext!,
      duration: const Duration(milliseconds: 800),
      curve: Curves.easeInOut,
    );
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GradientScaffold(
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('ROOMMET'),
      ),
      drawer: const AppDrawer(),
      child: SafeArea(
        child: SingleChildScrollView(
          controller: _scrollController,
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 30),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ── Hero Section ──────────────────────────────────
              Center(
                child: Column(
                  children: [
                    Container(
                      height: 100,
                      width: 100,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(color: AppTheme.accent, width: 2),
                        boxShadow: [
                          BoxShadow(
                            color: AppTheme.accent.withOpacity(0.35),
                            blurRadius: 30,
                            spreadRadius: 2,
                          ),
                        ],
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(22),
                        child: Image.asset(
                          'assets/images/logo.jpg',
                          fit: BoxFit.cover,
                          errorBuilder: (context, error, stackTrace) {
                            return Container(
                              color: AppTheme.bgSurface,
                              child: const Icon(
                                Icons.home_work_rounded,
                                size: 50,
                                color: AppTheme.accent,
                              ),
                            );
                          },
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),
                    ShaderMask(
                      shaderCallback: (bounds) => const LinearGradient(
                        colors: [AppTheme.textPrimary, AppTheme.accent, AppTheme.accentGlow],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ).createShader(bounds),
                      child: const Text(
                        'ROOMMET',
                        style: TextStyle(
                          fontSize: 42,
                          fontWeight: FontWeight.w900,
                          letterSpacing: 2,
                          color: Colors.white,
                        ),
                      ),
                    ),
                    const SizedBox(height: 10),
                    const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 16),
                      child: Text(
                        'A modern, digital-first resident directory featuring individual room allotment, secure access, and dynamic QR profiling.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: AppTheme.textSecondary,
                          fontSize: 14,
                          height: 1.5,
                        ),
                      ),
                    ),
                    const SizedBox(height: 30),
                    Row(
                      children: [
                        Expanded(
                          child: PrimaryButton(
                            label: '🔍 Discover Hostels',
                            onPressed: _scrollToDiscovery,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () => context.push('/login'),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: Colors.white,
                              side: BorderSide(color: Colors.white.withOpacity(0.15)),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                              padding: const EdgeInsets.symmetric(vertical: 14),
                            ),
                            child: const Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.vpn_key_rounded, size: 16),
                                SizedBox(width: 6),
                                Text(
                                  'Access Portal',
                                  style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 40),

              // ── Discovery Section ─────────────────────────────
              Container(
                key: _discoveryKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text(
                      'Public Hostels',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 12),
                    if (_loadingHostels)
                      const Center(
                        child: Padding(
                          padding: EdgeInsets.all(20),
                          child: CircularProgressIndicator(color: AppTheme.accent),
                        ),
                      )
                    else if (_hostelError != null)
                      GlassCard(
                        child: Column(
                          children: [
                            Text(
                              _hostelError!,
                              textAlign: TextAlign.center,
                              style: const TextStyle(color: AppTheme.danger),
                            ),
                            const SizedBox(height: 10),
                            TextButton(
                              onPressed: _fetchPublicHostels,
                              child: const Text('Retry'),
                            ),
                          ],
                        ),
                      )
                    else if (_hostels != null && _hostels!.isEmpty)
                      const GlassCard(
                        child: Padding(
                          padding: EdgeInsets.all(20),
                          child: Text(
                            'No public hostels available at the moment.',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: AppTheme.textSecondary),
                          ),
                        ),
                      )
                    else if (_hostels != null)
                      ListView.separated(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: _hostels!.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 12),
                        itemBuilder: (context, index) {
                          final hostel = _hostels![index];
                          final facilities = (hostel['facilities'] as List<dynamic>?)?.join(', ') ?? 'None';
                          return GlassCard(
                            padding: const EdgeInsets.all(18),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Expanded(
                                      child: Text(
                                        hostel['name'] ?? 'Unnamed Hostel',
                                        style: const TextStyle(
                                          fontSize: 18,
                                          fontWeight: FontWeight.bold,
                                          color: AppTheme.textPrimary,
                                        ),
                                      ),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                      decoration: BoxDecoration(
                                        color: AppTheme.accent.withOpacity(0.15),
                                        borderRadius: BorderRadius.circular(6),
                                      ),
                                      child: Text(
                                        hostel['code'] ?? '',
                                        style: const TextStyle(
                                          fontSize: 11,
                                          color: AppTheme.accent,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                Row(
                                  children: [
                                    const Icon(Icons.location_on_rounded, size: 14, color: AppTheme.textSecondary),
                                    const SizedBox(width: 4),
                                    Text(
                                      hostel['location'] ?? 'Unknown Location',
                                      style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      'Rent: ₹${hostel['rent'] ?? 'N/A'}',
                                      style: const TextStyle(
                                        color: AppTheme.success,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 14,
                                      ),
                                    ),
                                    Text(
                                      'Available Rooms: ${hostel['available_rooms'] ?? 0} / ${hostel['capacity'] ?? 0}',
                                      style: const TextStyle(
                                        color: AppTheme.textSecondary,
                                        fontSize: 12,
                                      ),
                                    ),
                                  ],
                                ),
                                if (facilities.isNotEmpty && facilities != 'None') ...[
                                  const Divider(color: Colors.white10, height: 16),
                                  Text(
                                    'Facilities: $facilities',
                                    style: const TextStyle(
                                      color: AppTheme.textSecondary,
                                      fontSize: 12,
                                      fontStyle: FontStyle.italic,
                                    ),
                                  ),
                                ],
                              ],
                            ),
                          );
                        },
                      )
                    else
                      const GlassCard(
                        child: Padding(
                          padding: EdgeInsets.all(20),
                          child: Text(
                            'Click "Discover Hostels" above to search and find public accommodation entries.',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: AppTheme.textSecondary),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 40),

              // ── Core Platform Pillars ─────────────────────────
              Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Center(
                    child: Column(
                      children: [
                        Text(
                          'Core Platform Pillars',
                          style: TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          'Everything required to run modern, paperless hostel communities.',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: AppTheme.textSecondary, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                  GridView.count(
                    crossAxisCount: 2,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    childAspectRatio: 1.1,
                    mainAxisSpacing: 12,
                    crossAxisSpacing: 12,
                    children: const [
                      _PillarCard(
                        emoji: '📱',
                        title: 'QR Identity Cards',
                        subtitle: 'Residents get dynamic QR codes for instant profiles.',
                      ),
                      _PillarCard(
                        emoji: '💳',
                        title: 'Fast UPI Payments',
                        subtitle: 'Scan owner UPI codes and upload receipts directly.',
                      ),
                      _PillarCard(
                        emoji: '📢',
                        title: 'Notice Bulletins',
                        subtitle: 'Post announcements to all residents at once.',
                      ),
                      _PillarCard(
                        emoji: '🔒',
                        title: 'Secure Privacy',
                        subtitle: 'Aadhaar data is masked, and files are secured.',
                      ),
                      _PillarCard(
                        emoji: '💬',
                        title: 'Direct Chat Room',
                        subtitle: 'Direct WhatsApp-style support conversation.',
                      ),
                      _PillarCard(
                        emoji: '⚡',
                        title: 'Mobile Adaptive',
                        subtitle: 'Highly responsive UX tailored for your device.',
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 40),

              // ── Operation Breakdown ───────────────────────────
              Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Center(
                    child: Column(
                      children: [
                        Text(
                          'Operation Breakdown',
                          style: TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          'Designed around clarity and minimal workflows.',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: AppTheme.textSecondary, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                  GlassCard(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              '👥',
                              style: TextStyle(
                                fontSize: 20,
                                shadows: [
                                  Shadow(
                                    color: AppTheme.accent.withOpacity(0.4),
                                    blurRadius: 10,
                                  )
                                ],
                              ),
                            ),
                            const SizedBox(width: 8),
                            const Text(
                              'For Residents',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: AppTheme.accent,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        const _BulletItem(text: 'Join using an owner\'s unique hostel code.'),
                        const _BulletItem(text: 'Access digital QR profile identity cards.'),
                        const _BulletItem(text: 'Upload billing UPI transaction screenshots.'),
                        const _BulletItem(text: 'Text direct support queries to managers.'),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  GlassCard(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              '🏢',
                              style: TextStyle(
                                fontSize: 20,
                                shadows: [
                                  Shadow(
                                    color: AppTheme.accent.withOpacity(0.4),
                                    blurRadius: 10,
                                  )
                                ],
                              ),
                            ),
                            const SizedBox(width: 8),
                            const Text(
                              'For Hostel Owners',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: AppTheme.accent,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        const _BulletItem(text: 'Control multiple hostels inside one account.'),
                        const _BulletItem(text: 'Approve or reject tenant dues in one tap.'),
                        const _BulletItem(text: 'Broadcast notices and mail alerts automatically.'),
                        const _BulletItem(text: 'Scan tenant QR codes to verify ledgers instantly.'),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 30),
            ],
          ),
        ),
      ),
    );
  }
}

class _PillarCard extends StatelessWidget {
  final String emoji;
  final String title;
  final String subtitle;

  const _PillarCard({
    required this.emoji,
    required this.title,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            emoji,
            style: const TextStyle(fontSize: 20),
          ),
          const SizedBox(height: 6),
          Text(
            title,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.bold,
              color: AppTheme.textPrimary,
            ),
          ),
          const SizedBox(height: 2),
          Expanded(
            child: Text(
              subtitle,
              style: const TextStyle(
                fontSize: 10,
                color: AppTheme.textSecondary,
                height: 1.3,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _BulletItem extends StatelessWidget {
  final String text;

  const _BulletItem({required this.text});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '•',
            style: TextStyle(color: AppTheme.textSecondary, fontSize: 16, height: 1.2),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 12,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
