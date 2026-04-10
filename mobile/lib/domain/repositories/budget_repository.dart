import 'package:ecole_platform/domain/entities/budget.dart';

abstract class BudgetRepository {
  Future<List<BudgetEnvelope>> listBudgets({
    Map<String, dynamic>? params,
  });

  Future<BudgetEnvelope> createBudget(Map<String, dynamic> payload);

  Future<BudgetEnvelope> getBudgetDetail(String id);

  Future<BudgetEnvelope> updateBudget(String id, Map<String, dynamic> payload);

  Future<void> deleteBudget(String id);

  Future<List<BudgetAllocation>> getBudgetAllocations(String id);

  Future<BudgetAllocation> createAllocation(
    String budgetId,
    Map<String, dynamic> payload,
  );

  Future<BudgetAllocation> getAllocation(String allocationId);

  Future<BudgetAllocation> updateAllocation(
    String allocationId,
    Map<String, dynamic> payload,
  );

  Future<List<BudgetRequest>> getAllocationRequests(
    String allocationId, {
    Map<String, dynamic>? params,
  });

  Future<List<BudgetRequest>> listBudgetRequests({
    Map<String, dynamic>? params,
  });

  Future<BudgetRequest> createBudgetRequest(Map<String, dynamic> payload);

  Future<BudgetRequest> approveBudgetRequest(
    String id, {
    String? reviewComment,
  });

  Future<BudgetRequest> rejectBudgetRequest(
    String id, {
    String? reviewComment,
  });

  Future<List<BudgetTransaction>> getBudgetTransactions(String budgetId);

  Future<BudgetAnalytics> getBudgetAnalytics();

  Future<BudgetRequest> getBudgetRequest(String requestId);

  Future<BudgetTransaction> createTransaction(
    String allocationId,
    Map<String, dynamic> payload,
  );

  Future<List<BudgetTransaction>> getTransactions(String allocationId);
}
