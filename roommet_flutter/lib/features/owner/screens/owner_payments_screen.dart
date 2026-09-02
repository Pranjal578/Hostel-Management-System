import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

class OwnerPaymentsScreen extends ConsumerStatefulWidget {
  const OwnerPaymentsScreen({super.key});
  @override
  ConsumerState<OwnerPaymentsScreen> createState() => _OwnerPaymentsScreenState();
}

class _OwnerPaymentsScreenState extends ConsumerState<OwnerPaymentsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabs;
  List<dynamic> _payments = [];
  bool _loading = true;
  String _activeStatus = 'Pending';

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 3, vsync: this);
    _tabs.addListener(() {
      final statuses = ['Pending', 'Verified', 'Rejected'];
      setState(() => _activeStatus = statuses[_tabs.index]);
      _load();
    });
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final data = await ApiService().getOwnerPayments(status: _activeStatus);
      setState(() {
        _payments = data['payments'] as List? ?? [];
        _loading = false;
      });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  Future<void> _action(int paymentId, String action) async {
    String? reason;
    if (action == 'reject') {
      final ctrl = TextEditingController();
      reason = await showDialog<String>(
        context: context,
        builder: (_) => AlertDialog(
          backgroundColor: AppTheme.bgCard,
          title: const Text('Reject Payment',
              style: TextStyle(color: AppTheme.textPrimary)),
          content: TextField(
            controller: ctrl,
            style: const TextStyle(color: AppTheme.textPrimary),
            decoration: const InputDecoration(labelText: 'Reason (optional)'),
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Cancel',
                    style: TextStyle(color: AppTheme.textSecondary))),
            ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: AppTheme.danger),
                onPressed: () => Navigator.pop(context, ctrl.text),
                child: const Text('Reject')),
          ],
        ),
      );
      if (reason == null) return;
    }
    await ApiService().verifyPayment(paymentId, action, reason: reason);
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return GradientScaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(kToolbarHeight + 48),
        child: AppBar(
          backgroundColor: Colors.transparent,
          title: const Text('Payments',
              style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w600)),
          centerTitle: true,
          bottom: TabBar(
            controller: _tabs,
            indicatorColor: AppTheme.accent,
            labelColor: AppTheme.accent,
            unselectedLabelColor: AppTheme.textMuted,
            tabs: const [
              Tab(text: 'Pending'),
              Tab(text: 'Verified'),
              Tab(text: 'Rejected'),
            ],
          ),
        ),
      ),
      child: _loading
          ? const ShimmerList(count: 5, itemHeight: 120)
          : _payments.isEmpty
              ? const EmptyState(
                  icon: Icons.receipt_long_rounded,
                  title: 'No Payments',
                  subtitle: 'No payments in this category.')
              : RefreshIndicator(
                  color: AppTheme.accent,
                  onRefresh: _load,
                  child: ListView.builder(
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 100),
                    itemCount: _payments.length,
                    itemBuilder: (_, i) {
                      final p = _payments[i] as Map<String, dynamic>;
                      return _PaymentVerifyCard(
                        payment: p,
                        onApprove: _activeStatus == 'Pending'
                            ? () => _action(p['id'] as int, 'approve')
                            : null,
                        onReject: _activeStatus == 'Pending'
                            ? () => _action(p['id'] as int, 'reject')
                            : null,
                      );
                    },
                  ),
                ),
    );
  }
}

class _PaymentVerifyCard extends StatelessWidget {
  final Map<String, dynamic> payment;
  final VoidCallback? onApprove;
  final VoidCallback? onReject;
  const _PaymentVerifyCard(
      {required this.payment, this.onApprove, this.onReject});

  @override
  Widget build(BuildContext context) {
    final status = payment['status'] as String? ?? 'Pending';
    final screenshotPath = payment['screenshot_path'] as String?;
    return GlassCard(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(payment['resident_name'] ?? 'Resident',
                        style: const TextStyle(
                            color: AppTheme.textPrimary,
                            fontSize: 15,
                            fontWeight: FontWeight.w600)),
                    Text(payment['hostel_name'] ?? '',
                        style: const TextStyle(
                            color: AppTheme.textSecondary, fontSize: 12)),
                  ],
                ),
              ),
              StatusBadge(status),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              _info('Amount', '₹${payment['amount']}'),
              _info('Date', payment['payment_date'] ?? ''),
              _info('Txn ID', payment['transaction_id'] ?? ''),
            ],
          ),
          // View Receipt button (always visible when receipt exists)
          if (screenshotPath != null) ...[
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: () => showReceiptDialog(
                context,
                screenshotPath: screenshotPath,
                title: '${payment['resident_name'] ?? 'Resident'} — ₹${payment['amount']}',
              ),
              icon: const Icon(Icons.visibility_rounded, size: 16),
              label: const Text('View Receipt Proof'),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppTheme.accent,
                side: const BorderSide(color: AppTheme.accent),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10)),
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                textStyle: const TextStyle(fontSize: 13),
              ),
            ),
          ],
          if (onApprove != null || onReject != null) ...[
            const SizedBox(height: 14),
            const Divider(color: AppTheme.divider, height: 1),
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: PrimaryButton(
                    label: 'Approve',
                    icon: Icons.check_circle_rounded,
                    onPressed: onApprove,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                    child: DangerButton(label: 'Reject', onPressed: onReject)),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _info(String label, String value) => Expanded(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label,
                style: const TextStyle(
                    color: AppTheme.textMuted, fontSize: 10)),
            Text(value,
                style: const TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 13,
                    fontWeight: FontWeight.w600),
                overflow: TextOverflow.ellipsis),
          ],
        ),
      );
}
