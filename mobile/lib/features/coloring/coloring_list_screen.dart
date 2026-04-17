import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/features/coloring/coloring_provider.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/widgets/app_error_widget.dart';
import 'package:ecole_platform/shared/ui/widgets/kids_skeleton_layouts.dart';
import 'package:ecole_platform/shared/widgets/app_empty_state.dart';

class ColoringListScreen extends ConsumerWidget {
  const ColoringListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final coloringAsync = ref.watch(coloringProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Coloring Pages'),
      ),
      body: coloringAsync.when(
        loading: () => const ColoringGridSkeleton(),
        error: (error, _) => AppErrorWidget(
          message: '$error',
          onRetry: () => ref.read(coloringProvider.notifier).refresh(),
        ),
        data: (pages) {
          if (pages.isEmpty) {
            return RefreshIndicator(
              onRefresh: () => ref.read(coloringProvider.notifier).refresh(),
              child: ListView(
                children: const <Widget>[
                  SizedBox(height: 40),
                  AppEmptyState(
                    icon: Icons.palette_outlined,
                    title: 'لا توجد صفحات تلوين',
                    subtitle: 'سيضيف معلمك صفحات تلوين قريباً',
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () => ref.read(coloringProvider.notifier).refresh(),
            child: LayoutBuilder(
              builder: (context, constraints) {
                final crossAxisCount = constraints.maxWidth >= 900
                    ? 4
                    : constraints.maxWidth >= 640
                        ? 3
                        : 2;
                return GridView.builder(
                  padding: const EdgeInsets.all(AppSpacing.base),
                  gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: crossAxisCount,
                    crossAxisSpacing: AppSpacing.md,
                    mainAxisSpacing: AppSpacing.md,
                    childAspectRatio: 0.78,
                  ),
                  itemCount: pages.length,
                  itemBuilder: (context, index) {
                    final page = pages[index];
                    return _ColoringPageCard(
                      page: page,
                      imageHeaders: _imageHeaders(ref),
                      onTap: () => context.push('/coloring/${page.id}'),
                    );
                  },
                );
              },
            ),
          );
        },
      ),
    );
  }

  static Map<String, String> _imageHeaders(WidgetRef ref) {
    final token = ref.read(apiClientProvider).accessToken;
    if (token == null || token.isEmpty) {
      return const <String, String>{};
    }
    return <String, String>{'Authorization': 'Bearer $token'};
  }
}

class _ColoringPageCard extends StatelessWidget {
  const _ColoringPageCard({
    required this.page,
    required this.imageHeaders,
    required this.onTap,
  });

  final ColoringPageEntry page;
  final Map<String, String> imageHeaders;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(24),
        side: BorderSide(color: Colors.black.withAlpha(22)),
      ),
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Expanded(
              child: Container(
                width: double.infinity,
                color: Colors.white,
                child: Image.network(
                  page.imageUrl,
                  headers: imageHeaders,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => const _ThumbnailFallback(),
                  loadingBuilder: (context, child, loadingProgress) {
                    if (loadingProgress == null) {
                      return child;
                    }
                    return const Center(child: CircularProgressIndicator());
                  },
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(AppSpacing.sm),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    page.contentTitle,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.w800,
                        ),
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Row(
                    children: <Widget>[
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: AppSpacing.xs,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: KidsContentColors.storyBackground,
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                          page.asset.pageNumber == null
                              ? 'Color'
                              : 'Page ${page.asset.pageNumber}',
                          style:
                              Theme.of(context).textTheme.labelSmall?.copyWith(
                                    fontWeight: FontWeight.w700,
                                  ),
                        ),
                      ),
                      const Spacer(),
                      const Icon(Icons.brush_outlined, size: 18),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ThumbnailFallback extends StatelessWidget {
  const _ThumbnailFallback();

  @override
  Widget build(BuildContext context) {
    return Container(
      color: KidsContentColors.storyBackground,
      child: const Center(
        child: Icon(
          Icons.palette_outlined,
          size: 52,
          color: KidsContentColors.storyPageTurn,
        ),
      ),
    );
  }
}
