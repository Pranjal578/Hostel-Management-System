import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/features/auth/providers/auth_provider.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';

class OtpScreen extends ConsumerStatefulWidget {
  final String email;
  const OtpScreen({super.key, required this.email});
  @override
  ConsumerState<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends ConsumerState<OtpScreen> {
  final List<TextEditingController> _ctls =
      List.generate(6, (_) => TextEditingController());
  final List<FocusNode> _nodes = List.generate(6, (_) => FocusNode());

  @override
  void dispose() {
    for (final c in _ctls) c.dispose();
    for (final n in _nodes) n.dispose();
    super.dispose();
  }

  String get _otp => _ctls.map((c) => c.text).join();

  void _submit() {
    if (_otp.length != 6) return;
    ref.read(authProvider.notifier).verifyOtp(widget.email, _otp);
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);

    ref.listen(authProvider, (_, next) {
      if (next.status == AuthStatus.authenticated) {
        final role = next.role;
        if (role == 'Resident')    context.go('/resident');
        if (role == 'HostelOwner') context.go('/owner');
        if (role == 'SuperAdmin')  context.go('/admin');
        if (role == 'ShopOwner')   context.go('/shop');
      }
    });

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(gradient: AppTheme.bgGradient),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(28),
              child: Column(
                children: [
                  const Icon(Icons.security_rounded,
                      size: 64, color: AppTheme.accent),
                  const SizedBox(height: 16),
                  const Text('2-Factor Verification',
                      style: TextStyle(
                          color: AppTheme.textPrimary,
                          fontSize: 22,
                          fontWeight: FontWeight.w700)),
                  const SizedBox(height: 8),
                  Text(
                    'We sent a 6-digit code to\n${widget.email}',
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                        color: AppTheme.textSecondary, fontSize: 14),
                  ),
                  const SizedBox(height: 32),

                  GlassCard(
                    padding: const EdgeInsets.all(28),
                    child: Column(
                      children: [
                        // OTP boxes
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: List.generate(6, (i) => _buildOtpBox(i)),
                        ),

                        if (auth.error != null) ...[
                          const SizedBox(height: 16),
                          Text(auth.error!,
                              style: const TextStyle(
                                  color: AppTheme.danger, fontSize: 13)),
                        ],

                        const SizedBox(height: 24),
                        PrimaryButton(
                          label: 'Verify',
                          icon: Icons.check_circle_outline,
                          onPressed: _otp.length == 6 ? _submit : null,
                          isLoading: auth.isLoading,
                        ),
                        const SizedBox(height: 16),
                        TextButton(
                          onPressed: () => context.go('/login'),
                          child: const Text('← Back to login',
                              style: TextStyle(color: AppTheme.textSecondary)),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildOtpBox(int index) {
    return SizedBox(
      width: 44,
      height: 52,
      child: TextField(
        controller: _ctls[index],
        focusNode: _nodes[index],
        textAlign: TextAlign.center,
        keyboardType: TextInputType.number,
        maxLength: 1,
        style: const TextStyle(
            color: AppTheme.textPrimary,
            fontSize: 22,
            fontWeight: FontWeight.w700),
        decoration: InputDecoration(
          counterText: '',
          filled: true,
          fillColor: AppTheme.bgSurface,
          border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: AppTheme.divider)),
          focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: AppTheme.accent, width: 2)),
          contentPadding: EdgeInsets.zero,
        ),
        onChanged: (val) {
          if (val.isNotEmpty && index < 5) {
            _nodes[index + 1].requestFocus();
          } else if (val.isEmpty && index > 0) {
            _nodes[index - 1].requestFocus();
          }
          if (index == 5 && val.isNotEmpty) _submit();
          setState(() {});
        },
      ),
    );
  }
}
