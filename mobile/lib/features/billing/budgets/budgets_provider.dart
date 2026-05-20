import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/billing/budget.dart';

final budgetsProvider = FutureProvider<List<BudgetEnvelope>>((ref) async {
  return ref.read(budgetRepositoryProvider).listBudgets();
});

final budgetAnalyticsProvider = FutureProvider<BudgetAnalytics>((ref) async {
  return ref.read(budgetRepositoryProvider).getBudgetAnalytics();
});

final budgetRequestsProvider = FutureProvider<List<BudgetRequest>>((ref) async {
  return ref.read(budgetRepositoryProvider).listBudgetRequests();
});

final budgetDetailProvider =
    FutureProvider.family<BudgetDetailBundle, String>((ref, budgetId) async {
  final repository = ref.read(budgetRepositoryProvider);
  final results = await Future.wait<dynamic>([
    repository.getBudgetDetail(budgetId),
    repository.getBudgetAllocations(budgetId),
    repository.getBudgetTransactions(budgetId),
    repository.listBudgetRequests(params: {'budget_id': budgetId}),
    repository.getBudgetAnalytics(),
  ]);

  return BudgetDetailBundle(
    budget: results[0] as BudgetEnvelope,
    allocations: results[1] as List<BudgetAllocation>,
    transactions: results[2] as List<BudgetTransaction>,
    requests: results[3] as List<BudgetRequest>,
    analytics: results[4] as BudgetAnalytics,
  );
});

class BudgetRequestActionNotifier extends AsyncNotifier<void> {
  @override
  Future<void> build() async {}

  Future<void> submit({
    required String budgetId,
    required double amount,
    required String description,
    required String justification,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      await ref.read(budgetRepositoryProvider).createBudgetRequest({
        'budget_id': budgetId,
        'amount': amount,
        'currency': 'MAD',
        'description': description,
        'justification': justification,
      });
      ref.invalidate(budgetRequestsProvider);
      ref.invalidate(budgetDetailProvider(budgetId));
    });
  }

  Future<void> approve(String requestId) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      await ref.read(budgetRepositoryProvider).approveBudgetRequest(requestId);
      ref.invalidate(budgetRequestsProvider);
    });
  }

  Future<void> reject(String requestId) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      await ref.read(budgetRepositoryProvider).rejectBudgetRequest(requestId);
      ref.invalidate(budgetRequestsProvider);
    });
  }
}

final budgetRequestActionProvider =
    AsyncNotifierProvider<BudgetRequestActionNotifier, void>(
  BudgetRequestActionNotifier.new,
);
