import 'package:flutter/material.dart';

import 'package:ecole_platform/shared/widgets/app_empty_state.dart';
import 'package:ecole_platform/shared/widgets/app_skeleton.dart';

class AppColumn<T> {
  final String header;
  final Widget Function(T row) cellBuilder;
  final double? width;
  final bool sortable;

  const AppColumn({
    required this.header,
    required this.cellBuilder,
    this.width,
    this.sortable = false,
  });
}

class AppDataTable<T> extends StatelessWidget {
  final List<AppColumn<T>> columns;
  final List<T> rows;
  final bool isLoading;
  final String emptyMessage;
  final ValueChanged<T>? onRowTap;

  const AppDataTable({
    super.key,
    required this.columns,
    required this.rows,
    this.isLoading = false,
    this.emptyMessage = 'No data available',
    this.onRowTap,
  });

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const AppSkeleton(
        variant: SkeletonVariant.tableRow,
        count: 5,
      );
    }

    if (rows.isEmpty) {
      return AppEmptyState(
        icon: Icons.inbox_outlined,
        title: emptyMessage,
      );
    }

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: DataTable(
        columns: columns
            .map(
              (column) => DataColumn(
                label: SizedBox(
                  width: column.width,
                  child: Text(column.header),
                ),
                tooltip: column.sortable ? '${column.header} (sortable)' : null,
              ),
            )
            .toList(),
        rows: List.generate(
          rows.length,
          (index) {
            final row = rows[index];
            return DataRow.byIndex(
              index: index,
              onSelectChanged: onRowTap == null ? null : (_) => onRowTap!(row),
              cells: columns
                  .map(
                    (column) => DataCell(
                      SizedBox(
                        width: column.width,
                        child: column.cellBuilder(row),
                      ),
                    ),
                  )
                  .toList(),
            );
          },
        ),
      ),
    );
  }
}
