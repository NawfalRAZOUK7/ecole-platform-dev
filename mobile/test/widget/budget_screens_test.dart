import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:intl/intl.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/domain/entities/billing/budget.dart';
import 'package:ecole_platform/features/billing/budgets/budget_detail_screen.dart';
import 'package:ecole_platform/features/billing/budgets/budget_list_screen.dart';
import 'package:ecole_platform/features/billing/budgets/budget_request_screen.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

void main() {
  group('Budget screens', () {
    setUpAll(registerTestFallbacks);

    testWidgets('BudgetListScreen renders analytics and budget cards',
        (tester) async {
      final budgetRepository = MockBudgetRepository();

      when(() => budgetRepository.listBudgets()).thenAnswer(
        (_) async => [_budgetEnvelope],
      );
      when(() => budgetRepository.getBudgetAnalytics()).thenAnswer(
        (_) async => _budgetAnalytics,
      );

      await pumpApp(
        tester,
        const BudgetListScreen(),
        overrides: buildMockRepositoryOverrides(
          budgetRepository: budgetRepository,
        ),
      );
      await _settle(tester);

      expect(find.text('STEM'), findsOneWidget);
      expect(find.textContaining('2000'), findsWidgets);
      expect(find.text(_formatMad(450)), findsOneWidget);
    });

    testWidgets('BudgetListScreen shows an empty state for no budgets',
        (tester) async {
      final budgetRepository = MockBudgetRepository();

      when(() => budgetRepository.listBudgets())
          .thenAnswer((_) async => const []);
      when(() => budgetRepository.getBudgetAnalytics()).thenAnswer(
        (_) async => _budgetAnalytics,
      );

      await pumpApp(
        tester,
        const BudgetListScreen(),
        overrides: buildMockRepositoryOverrides(
          budgetRepository: budgetRepository,
        ),
      );
      await _settle(tester);

      expect(find.byType(AppEmptyState), findsOneWidget);
    });

    testWidgets('BudgetListScreen renders repository errors', (tester) async {
      final budgetRepository = MockBudgetRepository();

      when(() => budgetRepository.listBudgets())
          .thenThrow(Exception('budgets failed'));
      when(() => budgetRepository.getBudgetAnalytics()).thenAnswer(
        (_) async => _budgetAnalytics,
      );

      await pumpApp(
        tester,
        const BudgetListScreen(),
        overrides: buildMockRepositoryOverrides(
          budgetRepository: budgetRepository,
        ),
      );
      await _settle(tester);

      expect(find.byType(AppErrorWidget), findsOneWidget);
      expect(find.textContaining('budgets failed'), findsOneWidget);
    });

    testWidgets('BudgetDetailScreen renders overview and allocations',
        (tester) async {
      final budgetRepository = MockBudgetRepository();

      when(() => budgetRepository.getBudgetDetail('budget-1')).thenAnswer(
        (_) async => _budgetEnvelope,
      );
      when(() => budgetRepository.getBudgetAllocations('budget-1')).thenAnswer(
        (_) async => [_allocation],
      );
      when(() => budgetRepository.getBudgetTransactions('budget-1')).thenAnswer(
        (_) async => [_transaction],
      );
      when(
        () => budgetRepository
            .listBudgetRequests(params: {'budget_id': 'budget-1'}),
      ).thenAnswer((_) async => [_request]);
      when(() => budgetRepository.getBudgetAnalytics()).thenAnswer(
        (_) async => _budgetAnalytics,
      );

      await pumpApp(
        tester,
        const BudgetDetailScreen(budgetId: 'budget-1'),
        overrides: buildMockRepositoryOverrides(
          budgetRepository: budgetRepository,
        ),
      );
      await _settle(tester);

      expect(find.text('STEM'), findsOneWidget);
      expect(find.text('Supplies'), findsOneWidget);
      expect(find.text(_formatMad(1550)), findsOneWidget);
    });

    testWidgets('BudgetDetailScreen switches across transactions and requests',
        (tester) async {
      final budgetRepository = MockBudgetRepository();

      when(() => budgetRepository.getBudgetDetail('budget-1')).thenAnswer(
        (_) async => _budgetEnvelope,
      );
      when(() => budgetRepository.getBudgetAllocations('budget-1')).thenAnswer(
        (_) async => [_allocation],
      );
      when(() => budgetRepository.getBudgetTransactions('budget-1')).thenAnswer(
        (_) async => [_transaction],
      );
      when(
        () => budgetRepository
            .listBudgetRequests(params: {'budget_id': 'budget-1'}),
      ).thenAnswer((_) async => [_request]);
      when(() => budgetRepository.getBudgetAnalytics()).thenAnswer(
        (_) async => _budgetAnalytics,
      );

      await pumpApp(
        tester,
        const BudgetDetailScreen(budgetId: 'budget-1'),
        overrides: buildMockRepositoryOverrides(
          budgetRepository: budgetRepository,
        ),
      );
      await _settle(tester);

      await tester.tap(find.text('Transactions'));
      await tester.pumpAndSettle();
      expect(find.text('Microscope purchase'), findsOneWidget);

      await tester.tap(find.text('Demandes'));
      await tester.pumpAndSettle();
      expect(find.text('Lab kits'), findsOneWidget);
    });

    testWidgets('BudgetRequestScreen renders the approval queue',
        (tester) async {
      final budgetRepository = MockBudgetRepository();

      when(() => budgetRepository.listBudgets()).thenAnswer(
        (_) async => [_budgetEnvelope],
      );
      when(() => budgetRepository.listBudgetRequests()).thenAnswer(
        (_) async => [_request],
      );
      when(() => budgetRepository.createBudgetRequest(any()))
          .thenAnswer((_) async => _request);
      when(
        () => budgetRepository.approveBudgetRequest(
          any(),
          reviewComment: any(named: 'reviewComment'),
        ),
      ).thenAnswer((_) async => _request);
      when(
        () => budgetRepository.rejectBudgetRequest(
          any(),
          reviewComment: any(named: 'reviewComment'),
        ),
      ).thenAnswer((_) async => _request);

      await pumpApp(
        tester,
        const BudgetRequestScreen(),
        overrides: buildMockRepositoryOverrides(
          budgetRepository: budgetRepository,
        ),
      );
      await _settle(tester);

      expect(find.text('Approval queue'), findsOneWidget);
      expect(find.text('Lab kits'), findsOneWidget);
      expect(find.text('Approve'), findsOneWidget);
      expect(find.text('Reject'), findsOneWidget);
    });

    testWidgets('BudgetRequestScreen submits new requests', (tester) async {
      final budgetRepository = MockBudgetRepository();

      when(() => budgetRepository.listBudgets()).thenAnswer(
        (_) async => [_budgetEnvelope],
      );
      when(() => budgetRepository.listBudgetRequests()).thenAnswer(
        (_) async => [_request],
      );
      when(() => budgetRepository.createBudgetRequest(any())).thenAnswer(
        (_) async => _request,
      );
      when(
        () => budgetRepository.approveBudgetRequest(
          any(),
          reviewComment: any(named: 'reviewComment'),
        ),
      ).thenAnswer((_) async => _request);
      when(
        () => budgetRepository.rejectBudgetRequest(
          any(),
          reviewComment: any(named: 'reviewComment'),
        ),
      ).thenAnswer((_) async => _request);

      await pumpApp(
        tester,
        const BudgetRequestScreen(),
        overrides: buildMockRepositoryOverrides(
          budgetRepository: budgetRepository,
        ),
      );
      await _settle(tester);

      await tester.enterText(find.byType(TextFormField).at(0), '250');
      await tester.enterText(find.byType(TextFormField).at(1), 'Printer paper');
      await tester.enterText(
        find.byType(TextFormField).at(2),
        'Needed for exams',
      );
      await tester.tap(find.byIcon(Icons.send_outlined));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      final captured = verify(
        () => budgetRepository.createBudgetRequest(captureAny()),
      ).captured.single as Map<String, dynamic>;

      expect(captured['budget_id'], 'budget-1');
      expect(captured['amount'], 250.0);
      expect(captured['description'], 'Printer paper');
      expect(find.text('Budget request submitted'), findsOneWidget);
    });
  });
}

const _budgetEnvelope = BudgetEnvelope(
  id: 'budget-1',
  name: 'STEM',
  code: 'B-1',
  status: 'active',
  totalAmount: 2000,
  allocatedAmount: 1200,
  spentAmount: 450,
  currency: 'MAD',
);

const _budgetAnalytics = BudgetAnalytics(
  totalBudget: 2000,
  allocatedAmount: 1200,
  spentAmount: 450,
  availableAmount: 1550,
  openRequests: 3,
);

const _allocation = BudgetAllocation(
  id: 'allocation-1',
  budgetId: 'budget-1',
  label: 'Supplies',
  amount: 800,
  committedAmount: 300,
  spentAmount: 150,
  currency: 'MAD',
);

const _transaction = BudgetTransaction(
  id: 'transaction-1',
  allocationId: 'allocation-1',
  amount: 150,
  currency: 'MAD',
  direction: 'outflow',
  description: 'Microscope purchase',
);

const _request = BudgetRequest(
  id: 'request-1',
  allocationId: 'allocation-1',
  budgetId: 'budget-1',
  status: 'pending',
  amount: 250,
  currency: 'MAD',
  description: 'Lab kits',
  justification: 'Hands-on science materials',
);

Future<void> _settle(WidgetTester tester) async {
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 100));
  await tester.pump(const Duration(milliseconds: 100));
}

String _formatMad(double amount) {
  return NumberFormat.currency(
    locale: 'fr_MA',
    symbol: 'MAD',
  ).format(amount);
}
