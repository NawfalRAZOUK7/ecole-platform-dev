import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/invoice.dart';

final billingStatusFilterProvider = StateProvider<String?>((ref) => null);

final siblingPolicyProvider = FutureProvider<SiblingPolicy>((ref) async {
  return ref.read(invoiceRepositoryProvider).getSiblingPolicy();
});

final lateFeePolicyProvider = FutureProvider<LateFeePolicy>((ref) async {
  return ref.read(invoiceRepositoryProvider).getLateFeePolicy();
});

final paymentPlansProvider = FutureProvider<List<PaymentPlan>>((ref) async {
  return ref.read(invoiceRepositoryProvider).listPaymentPlans(
        status: ref.watch(billingStatusFilterProvider),
      );
});

final paymentPlanProvider =
    FutureProvider.family<PaymentPlan, String>((ref, id) async {
  return ref.read(invoiceRepositoryProvider).getPaymentPlan(id);
});
