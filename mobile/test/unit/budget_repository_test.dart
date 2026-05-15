import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/data/repositories_impl/billing/budget_repository_impl.dart';

import '../helpers/api_responses.dart';
import '../helpers/test_mocks.dart';

void main() {
  setUpAll(registerTestFallbacks);

  test('lists budget envelopes', () async {
    final api = MockApiClient();
    final repository = BudgetRepositoryImpl(api: api);

    when(() => api.list('/budgets', params: null)).thenAnswer(
      (_) async => listResponse(
        const [
          {
            'id': 'budget-1',
            'name': 'STEM',
            'code': 'STEM-26',
            'status': 'active',
            'total_amount': 2000,
            'allocated_amount': 1500,
            'spent_amount': 450,
            'currency': 'MAD',
          },
        ],
      ),
    );

    final budgets = await repository.listBudgets();

    expect(budgets, hasLength(1));
    expect(budgets.single.availableAmount, 1550);
  });

  test('loads allocations for a budget', () async {
    final api = MockApiClient();
    final repository = BudgetRepositoryImpl(api: api);

    when(() => api.list('/budgets/budget-1/allocations')).thenAnswer(
      (_) async => listResponse(
        const [
          {
            'id': 'allocation-1',
            'budget_id': 'budget-1',
            'label': 'Supplies',
            'amount': 1200,
            'committed_amount': 300,
            'spent_amount': 200,
            'currency': 'MAD',
          },
        ],
      ),
    );

    final allocations = await repository.getBudgetAllocations('budget-1');

    expect(allocations.single.label, 'Supplies');
    expect(allocations.single.amount, 1200);
  });

  test('creates and approves a budget request', () async {
    final api = MockApiClient();
    final repository = BudgetRepositoryImpl(api: api);

    when(() => api.list('/budgets/budget-1/allocations')).thenAnswer(
      (_) async => listResponse(
        const [
          {
            'id': 'allocation-1',
            'budget_id': 'budget-1',
            'label': 'Lab kits',
            'amount': 1200,
            'committed_amount': 300,
            'spent_amount': 200,
            'currency': 'MAD',
          },
        ],
      ),
    );
    when(
      () => api.post(
        '/budgets/allocations/allocation-1/requests',
        body: const {
          'amount': 250,
          'currency': 'MAD',
          'description': 'Lab kits',
          'justification': 'Need supplies',
        },
      ),
    ).thenAnswer(
      (_) async => response(
        const {
          'id': 'request-1',
          'allocation_id': 'allocation-1',
          'budget_id': 'budget-1',
          'status': 'pending',
          'amount': 250,
          'currency': 'MAD',
          'description': 'Lab kits',
          'justification': 'Need supplies',
        },
      ),
    );
    when(
      () => api.post(
        '/budgets/requests/request-1/approve',
        body: const {'review_comment': 'approved'},
      ),
    ).thenAnswer(
      (_) async => response(
        const {
          'id': 'request-1',
          'allocation_id': 'allocation-1',
          'budget_id': 'budget-1',
          'status': 'approved',
          'amount': 250,
          'currency': 'MAD',
          'description': 'Lab kits',
        },
      ),
    );

    final created = await repository.createBudgetRequest(
      const {
        'budget_id': 'budget-1',
        'amount': 250,
        'currency': 'MAD',
        'description': 'Lab kits',
        'justification': 'Need supplies',
      },
    );
    final approved = await repository.approveBudgetRequest(
      'request-1',
      reviewComment: 'approved',
    );

    expect(created.allocationId, 'allocation-1');
    expect(approved.status, 'approved');
  });
}
