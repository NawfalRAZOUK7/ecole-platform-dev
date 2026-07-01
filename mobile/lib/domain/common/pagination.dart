/// Shared cursor-pagination value object for domain repository contracts.
class PaginatedList<T> {
  final List<T> items;
  final String? nextCursor;
  final bool hasMore;

  const PaginatedList({
    required this.items,
    this.nextCursor,
    required this.hasMore,
  });
}
