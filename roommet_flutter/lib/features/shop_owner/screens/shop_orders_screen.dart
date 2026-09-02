import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:roommet_flutter/core/network/api_service.dart';
import 'package:roommet_flutter/core/theme/app_theme.dart';
import 'package:roommet_flutter/shared/widgets/common_widgets.dart';
import 'package:roommet_flutter/shared/widgets/shimmer_widgets.dart';

class ShopOrdersScreen extends ConsumerStatefulWidget {
  const ShopOrdersScreen({super.key});

  @override
  ConsumerState<ShopOrdersScreen> createState() => _ShopOrdersScreenState();
}

class _ShopOrdersScreenState extends ConsumerState<ShopOrdersScreen> {
  List<dynamic> _orders = [];
  bool _loading = true;
  String _activeStatus = 'Pending';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final data = await ApiService().getShopOrders(status: _activeStatus.isEmpty ? null : _activeStatus);
      setState(() {
        _orders = data['orders'] as List? ?? [];
        _loading = false;
      });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  Future<void> _action(int orderId, String action) async {
    String? reason;
    if (action == 'reject') {
      final ctrl = TextEditingController();
      reason = await showDialog<String>(
        context: context,
        builder: (_) => AlertDialog(
          backgroundColor: AppTheme.bgCard,
          title: const Text('Reject Order', style: TextStyle(color: AppTheme.textPrimary)),
          content: TextField(
            controller: ctrl,
            style: const TextStyle(color: AppTheme.textPrimary),
            decoration: const InputDecoration(labelText: 'Reason for rejection'),
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Cancel', style: TextStyle(color: AppTheme.textSecondary))),
            ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: AppTheme.danger),
                onPressed: () => Navigator.pop(context, ctrl.text.trim()),
                child: const Text('Reject')),
          ],
        ),
      );
      if (reason == null) return;
    }

    try {
      await ApiService().updateOrderStatus(orderId, action, reason: reason);
      _load();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Action failed: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return GradientScaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(kToolbarHeight + 48),
        child: AppBar(
          backgroundColor: Colors.transparent,
          title: const Text('Shop Orders', style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w600)),
          centerTitle: true,
          bottom: TabBar(
            onTap: (idx) {
              final statuses = ['Pending', 'Confirmed', 'Rejected', ''];
              setState(() => _activeStatus = statuses[idx]);
              _load();
            },
            controller: TabController(length: 4, vsync: Scaffold.of(context)),
            indicatorColor: AppTheme.accent,
            labelColor: AppTheme.accent,
            unselectedLabelColor: AppTheme.textMuted,
            tabs: const [
              Tab(text: 'Pending'),
              Tab(text: 'Confirmed'),
              Tab(text: 'Rejected'),
              Tab(text: 'All'),
            ],
          ),
        ),
      ),
      child: _loading
          ? const ShimmerList(count: 4, itemHeight: 160)
          : _orders.isEmpty
              ? const EmptyState(
                  icon: Icons.receipt_long_rounded,
                  title: 'No Orders',
                  subtitle: 'No customer orders in this category.',
                )
              : RefreshIndicator(
                  color: AppTheme.accent,
                  onRefresh: _load,
                  child: ListView.builder(
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 100),
                    itemCount: _orders.length,
                    itemBuilder: (context, idx) {
                      final o = _orders[idx] as Map<String, dynamic>;
                      return _ShopOrderCard(
                        order: o,
                        onApprove: _activeStatus == 'Pending' ? () => _action(o['id'] as int, 'approve') : null,
                        onReject: _activeStatus == 'Pending' ? () => _action(o['id'] as int, 'reject') : null,
                        onAdvance: _activeStatus == 'Confirmed' && o['delivery_status'] != 'Delivered'
                            ? () => _action(o['id'] as int, 'advance')
                            : null,
                      );
                    },
                  ),
                ),
    );
  }
}

class _ShopOrderCard extends StatelessWidget {
  final Map<String, dynamic> order;
  final VoidCallback? onApprove;
  final VoidCallback? onReject;
  final VoidCallback? onAdvance;

  const _ShopOrderCard({
    required this.order,
    this.onApprove,
    this.onReject,
    this.onAdvance,
  });

  @override
  Widget build(BuildContext context) {
    final status = order['status'] as String? ?? 'Pending';
    final deliveryStatus = order['delivery_status'] as String? ?? 'Order Placed';

    return GlassCard(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  order['medicine_name'] ?? 'Order',
                  style: const TextStyle(color: AppTheme.textPrimary, fontSize: 16, fontWeight: FontWeight.w700),
                ),
              ),
              StatusBadge(status),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Buyer: ${order['buyer_name'] ?? 'Anonymous'}', style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
              Text('₹${order['total_price']}', style: const TextStyle(color: AppTheme.success, fontSize: 16, fontWeight: FontWeight.w700)),
            ],
          ),
          const SizedBox(height: 6),
          Text('Address: ${order['delivery_address'] ?? 'Not specified'}', style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
          Text('Phone: ${order['contact_phone'] ?? ''}', style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
          const SizedBox(height: 10),
          const Divider(color: AppTheme.divider, height: 1),
          const SizedBox(height: 10),
          Row(
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Delivery status', style: TextStyle(color: AppTheme.textMuted, fontSize: 10)),
                  Text(deliveryStatus, style: const TextStyle(color: AppTheme.accent, fontSize: 13, fontWeight: FontWeight.w600)),
                ],
              ),
              const Spacer(),
              if (onAdvance != null)
                ElevatedButton.icon(
                  onPressed: onAdvance,
                  icon: const Icon(Icons.airport_shuttle_rounded, size: 16),
                  label: const Text('Advance Step'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                  ),
                ),
            ],
          ),
          if (onApprove != null && onReject != null) ...[
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
                  child: DangerButton(
                    label: 'Reject',
                    onPressed: onReject,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
