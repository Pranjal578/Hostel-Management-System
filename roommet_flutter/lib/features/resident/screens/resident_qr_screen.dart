import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

final residentQrProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  return ApiService().getResidentQr();
});

class ResidentQrScreen extends ConsumerWidget {
  const ResidentQrScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final qrAsync = ref.watch(residentQrProvider);

    return GradientScaffold(
      appBar: RoommeetAppBar(title: 'My QR Identity'),
      child: qrAsync.when(
        loading: () => Center(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const ShimmerBox(width: 240, height: 240, borderRadius: 20),
            const SizedBox(height: 20),
            const ShimmerBox(width: 160, height: 16),
          ]),
        ),
        error: (e, _) => ErrorState(
          message: 'Could not load QR code',
          onRetry: () => ref.invalidate(residentQrProvider),
        ),
        data: (data) {
          final b64 = data['qr_base64'] as String?;
          final residentId = data['resident_id'];
          if (b64 == null) {
            return const EmptyState(
              icon: Icons.qr_code_rounded,
              title: 'QR Not Available',
              subtitle: 'Your QR code has not been generated yet.',
            );
          }
          final imgBytes = base64Decode(b64);
          return Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(32),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('Your Identity QR Code',
                      style: TextStyle(
                          color: AppTheme.textPrimary,
                          fontSize: 20,
                          fontWeight: FontWeight.w700)),
                  const SizedBox(height: 8),
                  const Text(
                    'Present this to your hostel owner for verification',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: AppTheme.textSecondary, fontSize: 14),
                  ),
                  const SizedBox(height: 32),
                  GlassCard(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: Image.memory(imgBytes, width: 220, height: 220),
                        ),
                        const SizedBox(height: 16),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 14, vertical: 8),
                          decoration: BoxDecoration(
                            color: AppTheme.bgSurface,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Text(
                            'Resident ID: #$residentId',
                            style: const TextStyle(
                                color: AppTheme.textSecondary,
                                fontSize: 13,
                                fontFamily: 'monospace'),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),
                  GlassCard(
                    padding: const EdgeInsets.all(14),
                    child: Row(
                      children: const [
                        Icon(Icons.info_outline_rounded,
                            color: AppTheme.info, size: 18),
                        SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            'This QR code links to your secure profile page. Only hostel staff can access your full details.',
                            style: TextStyle(
                                color: AppTheme.textSecondary, fontSize: 12),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
