import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/content_item.dart';

@immutable
class ColoringPageEntry {
  const ColoringPageEntry({
    required this.id,
    required this.contentItemId,
    required this.contentTitle,
    required this.asset,
  });

  final String id;
  final String contentItemId;
  final String contentTitle;
  final ContentItemAsset asset;

  String get imageUrl => asset.downloadUrl;

  String get title {
    final pageNumber = asset.pageNumber;
    if (pageNumber == null) {
      return contentTitle;
    }
    return '$contentTitle - Page $pageNumber';
  }
}

class ColoringNotifier extends AsyncNotifier<List<ColoringPageEntry>> {
  @override
  Future<List<ColoringPageEntry>> build() => _loadPages();

  Future<void> refresh() async {
    await ref.read(cacheStoreProvider).invalidatePrefix('content:');
    state = const AsyncLoading();
    state = await AsyncValue.guard(_loadPages);
  }

  Future<List<ColoringPageEntry>> _loadPages() async {
    final repo = ref.read(contentRepositoryProvider);
    final coloringItems = <ContentItem>[];
    String? cursor;
    bool hasMore = true;

    while (hasMore) {
      final page = await repo.getContentItems(
        cursor: cursor,
        contentType: ContentType.coloringBook.apiValue,
      );
      coloringItems.addAll(page.items);
      cursor = page.nextCursor;
      hasMore = page.hasMore && cursor != null;
    }

    final entries = <ColoringPageEntry>[];
    for (final item in coloringItems) {
      try {
        final assets = await repo.getStoryPages(item.id);
        for (final asset in assets) {
          entries.add(
            ColoringPageEntry(
              id: asset.id,
              contentItemId: item.id,
              contentTitle: item.title,
              asset: asset,
            ),
          );
        }
      } catch (_) {
        continue;
      }
    }

    entries.sort((left, right) {
      final titleCompare = left.contentTitle.compareTo(right.contentTitle);
      if (titleCompare != 0) {
        return titleCompare;
      }
      return (left.asset.pageNumber ?? 0)
          .compareTo(right.asset.pageNumber ?? 0);
    });
    return entries;
  }
}

final coloringProvider =
    AsyncNotifierProvider<ColoringNotifier, List<ColoringPageEntry>>(
  ColoringNotifier.new,
);

final coloringPageProvider =
    FutureProvider.autoDispose.family<ColoringPageEntry?, String>(
  (ref, pageId) async {
    final pages = await ref.watch(coloringProvider.future);
    for (final page in pages) {
      if (page.id == pageId) {
        return page;
      }
    }
    return null;
  },
);
