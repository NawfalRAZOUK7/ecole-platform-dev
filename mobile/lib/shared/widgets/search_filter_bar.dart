/// Reusable search bar + filter chips + sort toggle widget.
///
/// Reference: Phase 5B (from 3D) — Search & filter on mobile list screens.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/l10n/app_localizations.dart';

/// A single filter chip option.
class FilterOption {
  final String label;
  final String? value;

  const FilterOption({required this.label, this.value});
}

/// A named group of filter options.
///
/// [id] is a **stable logic identifier** (e.g. `'role'`, `'status'`) used by
/// callers in [SearchFilterBar.onFilterChanged] and as the key into
/// [SearchFilterBar.filterValues]. [label] is the **localized display text**
/// shown on the chip. Keeping the two separate decouples the displayed string
/// from the comparison logic, so the label can be translated freely without
/// breaking `key == ...` checks.
class FilterGroup {
  final String id;
  final String label;
  final List<FilterOption> options;

  const FilterGroup({
    required this.id,
    required this.label,
    required this.options,
  });
}

/// Search bar with optional filter chips and sort toggle.
class SearchFilterBar extends ConsumerWidget {
  final String? searchHint;
  final String searchValue;
  final ValueChanged<String> onSearchChanged;

  /// Filter groups, each with a stable [FilterGroup.id] and localized label.
  final List<FilterGroup> filters;

  /// Current selected values keyed by [FilterGroup.id].
  final Map<String, String?> filterValues;

  /// Called when a filter selection changes. [id] is the [FilterGroup.id].
  final void Function(String id, String? value)? onFilterChanged;

  /// Sort toggle.
  final bool showSort;
  final String? sortLabel;
  final bool sortAscending;
  final VoidCallback? onSortToggle;

  const SearchFilterBar({
    super.key,
    this.searchHint,
    this.searchValue = '',
    required this.onSearchChanged,
    this.filters = const [],
    this.filterValues = const {},
    this.onFilterChanged,
    this.showSort = false,
    this.sortLabel,
    this.sortAscending = true,
    this.onSortToggle,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final t = AppLocalizations.of(ref);
    const chipRowHeight = 56.0;

    return Semantics(
      container: true,
      label: t.t('common.searchAndFilter'),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: TextField(
              decoration: InputDecoration(
                hintText: searchHint ?? t.t('common.search'),
                prefixIcon: const Icon(Icons.search, size: 20),
                suffixIcon: searchValue.isNotEmpty
                    ? IconButton(
                        tooltip: t.t('common.clearSearch'),
                        icon: const Icon(Icons.clear),
                        onPressed: () => onSearchChanged(''),
                      )
                    : null,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
                contentPadding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
              ),
              controller: TextEditingController.fromValue(
                TextEditingValue(
                  text: searchValue,
                  selection:
                      TextSelection.collapsed(offset: searchValue.length),
                ),
              ),
              onChanged: onSearchChanged,
            ),
          ),
          if (filters.isNotEmpty || showSort)
            SizedBox(
              height: chipRowHeight,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                children: [
                  ...filters.map((group) {
                    final selected = filterValues[group.id];
                    final selectedLabel =
                        _selectedLabel(group.options, selected) ?? group.label;

                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(
                          minWidth: 48,
                          minHeight: 48,
                        ),
                        child: Semantics(
                          button: true,
                          label: t
                              .t('common.filterFor')
                              .replaceAll('{name}', group.label),
                          value: selectedLabel,
                          child: PopupMenuButton<String?>(
                            initialValue: selected,
                            onSelected: (value) =>
                                onFilterChanged?.call(group.id, value),
                            itemBuilder: (_) => group.options
                                .map(
                                  (option) => PopupMenuItem(
                                    value: option.value,
                                    child: Text(option.label),
                                  ),
                                )
                                .toList(),
                            child: Chip(
                              label: Text(
                                selectedLabel,
                                style: TextStyle(
                                  fontSize: 12,
                                  color: selected != null
                                      ? theme.colorScheme.primary
                                      : null,
                                ),
                              ),
                              avatar: selected != null
                                  ? Icon(
                                      Icons.filter_alt,
                                      size: 16,
                                      color: theme.colorScheme.primary,
                                    )
                                  : const Icon(Icons.filter_list, size: 16),
                              visualDensity: VisualDensity.standard,
                              materialTapTargetSize:
                                  MaterialTapTargetSize.padded,
                              side: selected != null
                                  ? BorderSide(color: theme.colorScheme.primary)
                                  : null,
                            ),
                          ),
                        ),
                      ),
                    );
                  }),
                  if (showSort)
                    ConstrainedBox(
                      constraints: const BoxConstraints(
                        minWidth: 48,
                        minHeight: 48,
                      ),
                      child: Semantics(
                        button: true,
                        label: t.t('common.sortOrder'),
                        value: sortLabel ??
                            (sortAscending
                                ? t.t('common.sortAscending')
                                : t.t('common.sortDescending')),
                        child: ActionChip(
                          label: Text(
                            sortLabel ?? (sortAscending ? 'A → Z' : 'Z → A'),
                            style: const TextStyle(fontSize: 12),
                          ),
                          avatar: Icon(
                            sortAscending
                                ? Icons.arrow_upward
                                : Icons.arrow_downward,
                            size: 16,
                          ),
                          onPressed: onSortToggle,
                          visualDensity: VisualDensity.standard,
                          materialTapTargetSize: MaterialTapTargetSize.padded,
                        ),
                      ),
                    ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  String? _selectedLabel(List<FilterOption> options, String? value) {
    if (value == null) return null;
    final match = options.where((o) => o.value == value);
    return match.isNotEmpty ? match.first.label : null;
  }
}
