import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

final residentPaymentsProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  return ApiService().getResidentPayments();
});

class ResidentPaymentsScreen extends ConsumerStatefulWidget {
  const ResidentPaymentsScreen({super.key});
  @override
  ConsumerState<ResidentPaymentsScreen> createState() => _ResidentPaymentsScreenState();
}

class _ResidentPaymentsScreenState extends ConsumerState<ResidentPaymentsScreen> {
  bool _showForm = false;
  final _amountCtrl = TextEditingController();
  final _txnCtrl    = TextEditingController();
  DateTime? _date;
  XFile? _receipt;
  bool _uploading = false;
  String? _error;

  @override
  void dispose() {
    _amountCtrl.dispose();
    _txnCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickFile() async {
    final picker = ImagePicker();
    final img = await picker.pickImage(source: ImageSource.gallery, imageQuality: 80);
    if (img != null) setState(() => _receipt = img);
  }

  Future<void> _submit() async {
    if (_amountCtrl.text.isEmpty || _txnCtrl.text.isEmpty || _date == null || _receipt == null) {
      setState(() => _error = 'Please fill all fields and select a receipt.');
      return;
    }
    setState(() { _uploading = true; _error = null; });
    try {
      await ApiService().submitPayment(
        amount: double.parse(_amountCtrl.text),
        transactionId: _txnCtrl.text.trim(),
        paymentDate: DateFormat('yyyy-MM-dd').format(_date!),
        filePath: _receipt!.path,
        fileName: _receipt!.name,
      );
      setState(() { _showForm = false; _uploading = false; });
      ref.invalidate(residentPaymentsProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Payment submitted successfully!')),
        );
      }
    } catch (e) {
      setState(() { _uploading = false; _error = e.toString(); });
    }
  }

  @override
  Widget build(BuildContext context) {
    final paymentsAsync = ref.watch(residentPaymentsProvider);

    return GradientScaffold(
      appBar: RoommeetAppBar(title: 'Payments', showBack: false),
      floatingActionButton: !_showForm
          ? FloatingActionButton.extended(
              onPressed: () => setState(() => _showForm = true),
              icon: const Icon(Icons.add),
              label: const Text('Submit Payment'),
            )
          : null,
      child: paymentsAsync.when(
        loading: () => const ShimmerList(count: 5),
        error: (e, _) => ErrorState(
          message: e.toString(),
          onRetry: () => ref.invalidate(residentPaymentsProvider),
        ),
        data: (data) {
          final payments = data['payments'] as List? ?? [];
          return ListView(
            padding: const EdgeInsets.fromLTRB(16, kToolbarHeight + 24, 16, 120),
            children: [
              if (_showForm) _buildUploadForm(),
              if (payments.isEmpty && !_showForm)
                EmptyState(
                  icon: Icons.receipt_long_rounded,
                  title: 'No Payments Yet',
                  subtitle: 'Tap the button below to submit your first payment',
                  action: null,
                )
              else ...[
                const Text('Payment History',
                    style: TextStyle(
                        color: AppTheme.textPrimary,
                        fontSize: 16,
                        fontWeight: FontWeight.w600)),
                const SizedBox(height: 12),
                ...payments.map((p) => _PaymentTile(p as Map<String, dynamic>)),
              ],
            ],
          );
        },
      ),
    );
  }

  Widget _buildUploadForm() {
    return GlassCard(
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text('Submit Payment',
                  style: TextStyle(
                      color: AppTheme.textPrimary,
                      fontSize: 17,
                      fontWeight: FontWeight.w600)),
              const Spacer(),
              IconButton(
                icon: const Icon(Icons.close, color: AppTheme.textSecondary),
                onPressed: () => setState(() => _showForm = false),
              ),
            ],
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _amountCtrl,
            keyboardType: TextInputType.number,
            style: const TextStyle(color: AppTheme.textPrimary),
            decoration: const InputDecoration(
              labelText: 'Amount (₹)',
              prefixIcon: Icon(Icons.currency_rupee_rounded, color: AppTheme.textSecondary),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _txnCtrl,
            style: const TextStyle(color: AppTheme.textPrimary),
            decoration: const InputDecoration(
              labelText: 'Transaction ID / UPI Ref',
              prefixIcon: Icon(Icons.tag_rounded, color: AppTheme.textSecondary),
            ),
          ),
          const SizedBox(height: 12),
          GestureDetector(
            onTap: () async {
              final d = await showDatePicker(
                context: context,
                initialDate: DateTime.now(),
                firstDate: DateTime(2024),
                lastDate: DateTime.now(),
                builder: (ctx, child) => Theme(
                  data: ThemeData.dark().copyWith(
                    colorScheme: const ColorScheme.dark(primary: AppTheme.accent),
                  ),
                  child: child!,
                ),
              );
              if (d != null) setState(() => _date = d);
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              decoration: BoxDecoration(
                color: AppTheme.bgSurface,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.divider),
              ),
              child: Row(
                children: [
                  const Icon(Icons.calendar_today_rounded,
                      color: AppTheme.textSecondary, size: 18),
                  const SizedBox(width: 10),
                  Text(
                    _date == null
                        ? 'Select Payment Date'
                        : DateFormat('dd MMM yyyy').format(_date!),
                    style: TextStyle(
                        color: _date == null
                            ? AppTheme.textMuted
                            : AppTheme.textPrimary),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          GestureDetector(
            onTap: _pickFile,
            child: Container(
              height: 80,
              decoration: BoxDecoration(
                color: AppTheme.bgSurface,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                    color: _receipt != null
                        ? AppTheme.success
                        : AppTheme.divider,
                    style: BorderStyle.solid),
              ),
              child: Center(
                child: _receipt == null
                    ? const Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.upload_file_rounded,
                              color: AppTheme.textMuted, size: 28),
                          SizedBox(height: 6),
                          Text('Tap to attach receipt',
                              style: TextStyle(
                                  color: AppTheme.textMuted, fontSize: 13)),
                        ],
                      )
                    : Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.check_circle_rounded,
                              color: AppTheme.success, size: 20),
                          const SizedBox(width: 8),
                          Text(_receipt!.name,
                              style: const TextStyle(
                                  color: AppTheme.success, fontSize: 13)),
                        ],
                      ),
              ),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 10),
            Text(_error!,
                style: const TextStyle(color: AppTheme.danger, fontSize: 13)),
          ],
          const SizedBox(height: 16),
          PrimaryButton(
            label: 'Submit Payment',
            icon: Icons.send_rounded,
            onPressed: _submit,
            isLoading: _uploading,
          ),
        ],
      ),
    );
  }
}

class _PaymentTile extends StatelessWidget {
  final Map<String, dynamic> payment;
  const _PaymentTile(this.payment);

  @override
  Widget build(BuildContext context) {
    final status = payment['status'] as String? ?? 'Pending';
    final screenshotPath = payment['screenshot_path'] as String?;
    return GlassCard(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(16),
      onTap: screenshotPath != null
          ? () => showReceiptDialog(
                context,
                screenshotPath: screenshotPath,
                title: '₹${payment['amount']} — ${payment['payment_date'] ?? ''}',
              )
          : null,
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppTheme.statusColor(status).withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              status == 'Verified'
                  ? Icons.check_circle_rounded
                  : status == 'Rejected'
                      ? Icons.cancel_rounded
                      : Icons.hourglass_empty_rounded,
              color: AppTheme.statusColor(status),
              size: 22,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '₹${payment['amount']}',
                  style: const TextStyle(
                      color: AppTheme.textPrimary,
                      fontSize: 17,
                      fontWeight: FontWeight.w700),
                ),
                Text(
                  payment['transaction_id'] ?? '',
                  style: const TextStyle(
                      color: AppTheme.textSecondary, fontSize: 12),
                ),
                Text(
                  payment['payment_date'] ?? '',
                  style: const TextStyle(
                      color: AppTheme.textMuted, fontSize: 11),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              StatusBadge(status),
              if (screenshotPath != null) ...[
                const SizedBox(height: 6),
                const Text(
                  'Tap to view receipt',
                  style: TextStyle(color: AppTheme.textMuted, fontSize: 10),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}

