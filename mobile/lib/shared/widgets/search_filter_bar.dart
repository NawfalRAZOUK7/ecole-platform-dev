/// Reusable search bar + filter chips + sort toggle widget.
///
/// Reference: Phase 5B (from 3D) — Search & filter on mobile list screens.

import 'package:flutter/material.dart';

/// A single filter chip option.
class FilterOption {
  final String label;
  final String? value;

  const FilterOption({required this.label, this.value});
}

/// Search bar with optional filter chips and sort toggle.
class SearchFilterBar extends StatelessWidget {
  final String? searchHint;
  final String searchValue;
  final ValueChanged<String> onSearchChanged;

  /// Named filter groups: key → list of options.
  final Map<String, List<FilterOption>> filters;

  /// Current selected values per filter key.
  final Map<String, String?> filterValues;

  /// Called when a filter selection changes.
  final void Function(String key, String? value)? onFilterChanged;

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
    this.filters = const {},
    this.filterValues = const {},
    this.onFilterChanged,
    this.showSort = false,
    this.sortLabel,
    this.sortAscending = true,
    this.onSortToggle,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    const chipRowHeight = 56.0;

    return Semantics(
      container: true,
      label: 'Search and filter controls',
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: TextField(
              decoration: InputDecoration(
                hintText: searchHint ?? 'Rechercher...',
                prefixIcon: const Icon(Icons.search, size: 20),
                suffixIcon: searchValue.isNotEmpty
                    ? IconButton(
                        tooltip: 'Clear search',
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
                  ...filters.entries.map((entry) {
                    final key = entry.key;
                    final options = entry.value;
                    final selected = filterValues[key];
                    final selectedLabel =
                        _selectedLabel(options, selected) ?? key;

                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(
                          minWidth: 48,
                          minHeight: 48,
                        ),
                        child: Semantics(
                          button: true,
                          label: '$key filter',
                          value: selectedLabel,
                          child: PopupMenuButton<String?>(
                            initialValue: selected,
                            onSelected: (value) =>
                                onFilterChanged?.call(key, value),
                            itemBuilder: (_) => options
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
                        label: 'Sort order',
                        value: sortLabel ??
                            (sortAscending ? 'Ascending' : 'Descending'),
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
