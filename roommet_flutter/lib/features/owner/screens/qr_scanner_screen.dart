import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';

class QrScannerScreen extends StatefulWidget {
  const QrScannerScreen({super.key});
  @override
  State<QrScannerScreen> createState() => _QrScannerScreenState();
}

class _QrScannerScreenState extends State<QrScannerScreen> {
  MobileScannerController? _ctrl;
  bool _scanned = false;
  bool _loading = false;
  Map<String, dynamic>? _residentData;
  String? _error;

  @override
  void initState() {
    super.initState();
    _ctrl = MobileScannerController();
  }

  @override
  void dispose() {
    _ctrl?.dispose();
    super.dispose();
  }

  Future<void> _onDetect(BarcodeCapture capture) async {
    if (_scanned || _loading) return;
    final code = capture.barcodes.first.rawValue ?? '';
    if (code.isEmpty) return;

    // Extract resident ID from URL like /profile/42
    final match = RegExp(r'/profile/(\d+)').firstMatch(code);
    if (match == null) {
      setState(() => _error = 'Invalid QR code. Not a ROOMMET profile code.');
      return;
    }
    final residentId = int.parse(match.group(1)!);
    setState(() { _scanned = true; _loading = true; });
    _ctrl?.stop();

    try {
      final data = await ApiService().getResidentDetail(residentId);
      setState(() { _residentData = data; _loading = false; });
    } catch (e) {
      setState(() {
        _error = 'Could not load resident data.';
        _loading = false;
      });
    }
  }

  void _reset() {
    setState(() { _scanned = false; _residentData = null; _error = null; });
    _ctrl?.start();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        title: const Text('Scan Resident QR',
            style: TextStyle(color: Colors.white)),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: _residentData != null
          ? _buildResult()
          : _loading
              ? const Center(
                  child: CircularProgressIndicator(color: AppTheme.accent))
              : Stack(
                  children: [
                    MobileScanner(
                        controller: _ctrl!, onDetect: _onDetect),
                    // Scan frame overlay
                    Center(
                      child: Container(
                        width: 240,
                        height: 240,
                        decoration: BoxDecoration(
                          border: Border.all(
                              color: AppTheme.accent, width: 3),
                          borderRadius: BorderRadius.circular(20),
                        ),
                      ),
                    ),
                    if (_error != null)
                      Positioned(
                        bottom: 100,
                        left: 20,
                        right: 20,
                        child: Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: AppTheme.danger.withOpacity(0.9),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(_error!,
                              textAlign: TextAlign.center,
                              style: const TextStyle(
                                  color: Colors.white, fontSize: 14)),
                        ),
                      ),
                    Positioned(
                      bottom: 40,
                      left: 0,
                      right: 0,
                      child: Center(
                        child: Text(
                          'Point camera at resident\'s QR code',
                          style: TextStyle(
                              color: Colors.white.withOpacity(0.7),
                              fontSize: 14),
                        ),
                      ),
                    ),
                  ],
                ),
    );
  }

  Widget _buildResult() {
    final r = _residentData!;
    final status = r['status'] as String? ?? '';
    final payStatus = r['payment_status'] as String? ?? 'None';

    return Container(
      decoration: const BoxDecoration(gradient: AppTheme.bgGradient),
      child: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            AccentCard(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  const Icon(Icons.verified_user_rounded,
                      color: Colors.white, size: 40),
                  const SizedBox(height: 12),
                  Text(r['full_name'] ?? '',
                      style: const TextStyle(
                          color: Colors.white,
                          fontSize: 22,
                          fontWeight: FontWeight.w700)),
                  Text(r['email'] ?? '',
                      style: TextStyle(
                          color: Colors.white.withOpacity(0.8), fontSize: 14)),
                  const SizedBox(height: 8),
                  StatusBadge(status),
                ],
              ),
            ),
            const SizedBox(height: 16),
            GlassCard(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  _row(Icons.meeting_room_rounded, 'Room',
                      r['room_number'] ?? 'Pending'),
                  _divider(),
                  _row(Icons.home_work_rounded, 'Hostel',
                      r['hostel_name'] ?? ''),
                  _divider(),
                  _row(Icons.payment_rounded, 'Payment Status', payStatus,
                      valueColor: AppTheme.statusColor(payStatus)),
                  _divider(),
                  _row(Icons.phone_rounded, 'Emergency Contact',
                      r['emergency_contact_phone'] ?? ''),
                ],
              ),
            ),
            const SizedBox(height: 20),
            PrimaryButton(
              label: 'Scan Another',
              icon: Icons.qr_code_scanner_rounded,
              onPressed: _reset,
            ),
          ],
        ),
      ),
    );
  }

  Widget _row(IconData icon, String label, String value, {Color? valueColor}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Row(
        children: [
          Icon(icon, color: AppTheme.textSecondary, size: 18),
          const SizedBox(width: 12),
          Text(label,
              style: const TextStyle(
                  color: AppTheme.textSecondary, fontSize: 13)),
          const Spacer(),
          Text(value,
              style: TextStyle(
                  color: valueColor ?? AppTheme.textPrimary,
                  fontSize: 13,
                  fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  Widget _divider() => const Divider(color: AppTheme.divider, height: 1);
}
