import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/domain/entities/billing/budget.dart';
import 'package:ecole_platform/domain/repositories/billing/budget_repository.dart';

class BudgetRepositoryImpl implements BudgetRepository {
  final ApiClient _api;

  BudgetRepositoryImpl({required ApiClient api}) : _api = api;

  @override
  Future<List<BudgetEnvelope>> listBudgets({
    Map<String, dynamic>? params,
  }) async {
    final response = await _api.list('/budgets', params: params);
    return response.data.map(BudgetEnvelope.fromJson).toList();
  }

  @override
  Future<BudgetEnvelope> createBudget(Map<String, dynamic> payload) async {
    final response = await _api.post('/budgets', body: payload);
    return BudgetEnvelope.fromJson(response.data);
  }

  @override
  Future<BudgetEnvelope> getBudgetDetail(String id) async {
    final response = await _api.get('/budgets/$id');
    return BudgetEnvelope.fromJson(response.data);
  }

  @override
  Future<BudgetEnvelope> updateBudget(
    String id,
    Map<String, dynamic> payload,
  ) async {
    final response = await _api.put('/budgets/$id', body: payload);
    return BudgetEnvelope.fromJson(response.data);
  }

  @override
  Future<void> deleteBudget(String id) async {
    await _api.delete('/budgets/$id');
  }

  @override
  Future<List<BudgetAllocation>> getBudgetAllocations(String id) async {
    final response = await _api.list('/budgets/$id/allocations');
    return response.data.map(BudgetAllocation.fromJson).toList();
  }

  @override
  Future<BudgetAllocation> createAllocation(
    String budgetId,
    Map<String, dynamic> payload,
  ) async {
    final response = await _api.post(
      '/budgets/$budgetId/allocations',
      body: payload,
    );
    return BudgetAllocation.fromJson(response.data);
  }

  @override
  Future<BudgetAllocation> getAllocation(String allocationId) async {
    final response = await _api.get('/budgets/allocations/$allocationId');
    return BudgetAllocation.fromJson(response.data);
  }

  @override
  Future<BudgetAllocation> updateAllocation(
    String allocationId,
    Map<String, dynamic> payload,
  ) async {
    final response = await _api.put(
      '/budgets/allocations/$allocationId',
      body: payload,
    );
    return BudgetAllocation.fromJson(response.data);
  }

  @override
  Future<List<BudgetRequest>> getAllocationRequests(
    String allocationId, {
    Map<String, dynamic>? params,
  }) async {
    final response = await _api.list(
      '/budgets/allocations/$allocationId/requests',
      params: params,
    );
    return response.data.map(BudgetRequest.fromJson).toList();
  }

  @override
  Future<List<BudgetRequest>> listBudgetRequests({
    Map<String, dynamic>? params,
  }) async {
    final budgetId = params?['budget_id']?.toString();
    final status = params?['status']?.toString();
    final budgets = budgetId == null
        ? await listBudgets()
        : <BudgetEnvelope>[await getBudgetDetail(budgetId)];

    final allRequests = <BudgetRequest>[];
    for (final budget in budgets) {
      final allocations = await getBudgetAllocations(budget.id);
      for (final allocation in allocations) {
        final requests = await getAllocationRequests(
          allocation.id,
          params: {
            if (status != null) 'status': status,
          },
        );
        allRequests.addAll(
          requests.map(
            (request) => BudgetRequest(
              id: request.id,
              allocationId: request.allocationId,
              budgetId: request.budgetId ?? budget.id,
              status: request.status,
              amount: request.amount,
              currency: request.currency,
              description: request.description,
              justification: request.justification,
              requesterName: request.requesterName,
              createdAt: request.createdAt,
            ),
          ),
        );
      }
    }
    return allRequests;
  }

  @override
  Future<BudgetRequest> createBudgetRequest(
    Map<String, dynamic> payload,
  ) async {
    final budgetId = payload['budget_id']?.toString();
    if (budgetId == null || budgetId.isEmpty) {
      throw ArgumentError('budget_id is required');
    }
    final allocations = await getBudgetAllocations(budgetId);
    final target = allocations.isEmpty ? null : allocations.first;
    if (target == null) {
      throw StateError('No allocations found for budget $budgetId');
    }
    final response = await _api.post(
      '/budgets/allocations/${target.id}/requests',
      body: {
        'amount': payload['amount'],
        'currency': payload['currency'] ?? 'MAD',
        'description': payload['description'],
        'justification': payload['justification'],
      },
    );
    return BudgetRequest.fromJson(response.data);
  }

  @override
  Future<BudgetRequest> approveBudgetRequest(
    String id, {
    String? reviewComment,
  }) async {
    final response = await _api.post(
      '/budgets/requests/$id/approve',
      body: {
        if (reviewComment != null) 'review_comment': reviewComment,
      },
    );
    return BudgetRequest.fromJson(response.data);
  }

  @override
  Future<BudgetRequest> rejectBudgetRequest(
    String id, {
    String? reviewComment,
  }) async {
    final response = await _api.post(
      '/budgets/requests/$id/reject',
      body: {
        if (reviewComment != null) 'review_comment': reviewComment,
      },
    );
    return BudgetRequest.fromJson(response.data);
  }

  @override
  Future<List<BudgetTransaction>> getBudgetTransactions(String budgetId) async {
    final allocations = await getBudgetAllocations(budgetId);
    final transactions = <BudgetTransaction>[];
    for (final allocation in allocations) {
      transactions.addAll(await getTransactions(allocation.id));
    }
    return transactions;
  }

  @override
  Future<BudgetAnalytics> getBudgetAnalytics() async {
    final response = await _api.get('/budgets/analytics');
    return BudgetAnalytics.fromJson(response.data);
  }

  @override
  Future<BudgetRequest> getBudgetRequest(String requestId) async {
    final response = await _api.get('/budgets/requests/$requestId');
    return BudgetRequest.fromJson(response.data);
  }

  @override
  Future<BudgetTransaction> createTransaction(
    String allocationId,
    Map<String, dynamic> payload,
  ) async {
    final response = await _api.post(
      '/budgets/allocations/$allocationId/transactions',
      body: payload,
    );
    return BudgetTransaction.fromJson(response.data);
  }

  @override
  Future<List<BudgetTransaction>> getTransactions(String allocationId) async {
    final response = await _api.list(
      '/budgets/allocations/$allocationId/transactions',
    );
    return response.data.map(BudgetTransaction.fromJson).toList();
  }
}
