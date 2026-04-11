import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ecole_platform/shared/widgets/widgets.dart';

import '../helpers/pump_app.dart';

class _TableRowData {
  final String name;
  final String role;

  const _TableRowData(this.name, this.role);
}

void main() {
  group('Shared widgets', () {
    testWidgets('AppBadge renders its label', (tester) async {
      await pumpApp(
        tester,
        const Center(
          child: AppBadge(label: 'Active', variant: AppBadgeVariant.success),
        ),
      );

      expect(find.text('Active'), findsOneWidget);
    });

    testWidgets('AppBadge exposes a semantics label', (tester) async {
      final semantics = tester.ensureSemantics();

      await pumpApp(
        tester,
        const Center(child: AppBadge(label: 'Pending')),
      );

      expect(find.bySemanticsLabel('Pending badge'), findsOneWidget);
      semantics.dispose();
    });

    testWidgets('AppDataTable shows a skeleton while loading', (tester) async {
      await pumpApp(
        tester,
        AppDataTable<_TableRowData>(
          columns: const [
            AppColumn(header: 'Name', cellBuilder: _cellPlaceholder),
          ],
          rows: const [],
          isLoading: true,
        ),
      );

      expect(find.byType(AppSkeleton), findsOneWidget);
    });

    testWidgets('AppDataTable shows an empty state when there are no rows',
        (tester) async {
      await pumpApp(
        tester,
        AppDataTable<_TableRowData>(
          columns: const [
            AppColumn(header: 'Name', cellBuilder: _cellPlaceholder),
          ],
          rows: const [],
          emptyMessage: 'No rows yet',
        ),
      );

      expect(find.text('No rows yet'), findsOneWidget);
      expect(find.byType(AppEmptyState), findsOneWidget);
    });

    testWidgets('AppDataTable renders headers and row cells', (tester) async {
      await pumpApp(
        tester,
        AppDataTable<_TableRowData>(
          columns: [
            AppColumn<_TableRowData>(
              header: 'Name',
              cellBuilder: (row) => Text(row.name),
            ),
            AppColumn<_TableRowData>(
              header: 'Role',
              cellBuilder: (row) => Text(row.role),
            ),
          ],
          rows: const [
            _TableRowData('Alice', 'Teacher'),
          ],
        ),
      );

      expect(find.text('Name'), findsOneWidget);
      expect(find.text('Role'), findsOneWidget);
      expect(find.text('Alice'), findsOneWidget);
      expect(find.text('Teacher'), findsOneWidget);
    });

    testWidgets('AppDataTable triggers row tap callbacks', (tester) async {
      _TableRowData? tapped;

      await pumpApp(
        tester,
        AppDataTable<_TableRowData>(
          columns: [
            AppColumn<_TableRowData>(
              header: 'Name',
              cellBuilder: (row) => Text(row.name),
            ),
          ],
          rows: const [
            _TableRowData('Alice', 'Teacher'),
          ],
          onRowTap: (row) => tapped = row,
        ),
      );

      await tester.tap(find.text('Alice'));
      await tester.pump();

      expect(tapped?.name, 'Alice');
    });

    testWidgets('AppStatCard renders label, value, and icon', (tester) async {
      await pumpApp(
        tester,
        const Center(
          child: AppStatCard(
            label: 'Attendance',
            value: '95%',
            icon: Icons.percent,
          ),
        ),
      );

      expect(find.text('Attendance'), findsOneWidget);
      expect(find.text('95%'), findsOneWidget);
      expect(find.byIcon(Icons.percent), findsOneWidget);
    });

    testWidgets('AppStatCard shows positive trend state', (tester) async {
      await pumpApp(
        tester,
        const Center(
          child: AppStatCard(
            label: 'Score',
            value: '18.0',
            trend: TrendDirection.up,
            trendValue: 12.5,
          ),
        ),
      );

      expect(find.byIcon(Icons.trending_up), findsOneWidget);
      expect(find.text('12.5%'), findsOneWidget);
    });

    testWidgets('AppStatCard shows negative trend state', (tester) async {
      await pumpApp(
        tester,
        const Center(
          child: AppStatCard(
            label: 'Score',
            value: '8.0',
            trend: TrendDirection.down,
            trendValue: 4.0,
          ),
        ),
      );

      expect(find.byIcon(Icons.trending_down), findsOneWidget);
      expect(find.text('4.0%'), findsOneWidget);
    });

    testWidgets('AppConfirmDialog returns true when confirmed', (tester) async {
      var result = false;

      await pumpApp(
        tester,
        Builder(
          builder: (context) => FilledButton(
            onPressed: () async {
              result = await AppConfirmDialog.show(
                context,
                title: 'Delete file',
                message: 'This action cannot be undone.',
              );
            },
            child: const Text('Open dialog'),
          ),
        ),
      );

      await tester.tap(find.text('Open dialog'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Confirm'));
      await tester.pumpAndSettle();

      expect(result, isTrue);
    });

    testWidgets('AppConfirmDialog invokes confirm callbacks', (tester) async {
      var callbackCalled = false;

      await pumpApp(
        tester,
        Builder(
          builder: (context) => FilledButton(
            onPressed: () {
              AppConfirmDialog.show(
                context,
                title: 'Archive',
                message: 'Archive this item?',
                onConfirm: () async {
                  callbackCalled = true;
                },
              );
            },
            child: const Text('Open dialog'),
          ),
        ),
      );

      await tester.tap(find.text('Open dialog'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Confirm'));
      await tester.pumpAndSettle();

      expect(callbackCalled, isTrue);
    });

    testWidgets('AppConfirmDialog returns false when cancelled',
        (tester) async {
      var result = true;

      await pumpApp(
        tester,
        Builder(
          builder: (context) => FilledButton(
            onPressed: () async {
              result = await AppConfirmDialog.show(
                context,
                title: 'Delete file',
                message: 'This action cannot be undone.',
              );
            },
            child: const Text('Open dialog'),
          ),
        ),
      );

      await tester.tap(find.text('Open dialog'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Cancel'));
      await tester.pumpAndSettle();

      expect(result, isFalse);
    });

    testWidgets('AppSkeleton renders the loading semantics label',
        (tester) async {
      final semantics = tester.ensureSemantics();

      await pumpApp(
        tester,
        const Center(
          child: AppSkeleton(variant: SkeletonVariant.tableRow, count: 3),
        ),
      );

      expect(find.bySemanticsLabel('Loading content'), findsOneWidget);
      semantics.dispose();
    });

    testWidgets('AppSkeleton builds circle placeholders', (tester) async {
      await pumpApp(
        tester,
        const Center(
          child: AppSkeleton(
            variant: SkeletonVariant.circle,
            count: 2,
          ),
        ),
      );

      expect(find.byType(AppSkeleton), findsOneWidget);
    });

    testWidgets('AppCurrencyText formats a MAD amount', (tester) async {
      await pumpApp(
        tester,
        const Center(child: AppCurrencyText(amount: 1234)),
      );

      expect(find.textContaining('MAD'), findsOneWidget);
    });

    testWidgets('AppEmptyState renders subtitle and action widgets',
        (tester) async {
      await pumpApp(
        tester,
        const AppEmptyState(
          icon: Icons.inbox_outlined,
          title: 'Nothing here',
          subtitle: 'Create your first item.',
          action: FilledButton(
            onPressed: null,
            child: Text('Create'),
          ),
        ),
      );

      expect(find.text('Nothing here'), findsOneWidget);
      expect(find.text('Create your first item.'), findsOneWidget);
      expect(find.text('Create'), findsOneWidget);
    });

    testWidgets('AppErrorWidget calls retry callbacks', (tester) async {
      var retried = false;

      await pumpApp(
        tester,
        AppErrorWidget(
          message: 'Something failed',
          onRetry: () => retried = true,
        ),
      );

      await tester.tap(find.text('Retry'));
      await tester.pump();

      expect(retried, isTrue);
    });

    testWidgets('AppFormField surfaces validation messages', (tester) async {
      final controller = TextEditingController();
      addTearDown(controller.dispose);

      await pumpApp(
        tester,
        Form(
          child: AppFormField(
            controller: controller,
            label: 'Email',
            hint: 'name@example.com',
            validator: (value) =>
                value == null || value.trim().isEmpty ? 'Required' : null,
          ),
        ),
      );

      await tester.enterText(find.byType(TextFormField), 'a');
      await tester.pump();
      await tester.enterText(find.byType(TextFormField), '');
      await tester.pump();

      expect(find.text('Required'), findsOneWidget);
    });

    testWidgets('SearchFilterBar clears the active search value',
        (tester) async {
      var currentSearch = 'hello';

      await pumpApp(
        tester,
        StatefulBuilder(
          builder: (context, setState) {
            return SearchFilterBar(
              searchValue: currentSearch,
              onSearchChanged: (value) {
                setState(() => currentSearch = value);
              },
            );
          },
        ),
      );

      await tester.tap(find.byTooltip('Clear search'));
      await tester.pump();

      expect(currentSearch, isEmpty);
    });

    testWidgets('SearchFilterBar toggles sort callbacks', (tester) async {
      var toggles = 0;

      await pumpApp(
        tester,
        SearchFilterBar(
          searchValue: '',
          onSearchChanged: (_) {},
          showSort: true,
          sortAscending: true,
          onSortToggle: () => toggles += 1,
        ),
      );

      await tester.tap(find.byType(ActionChip));
      await tester.pump();

      expect(toggles, 1);
    });
  });
}

Widget _cellPlaceholder(_TableRowData row) => Text(row.name);
