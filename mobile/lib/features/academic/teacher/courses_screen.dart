import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/widgets/shimmer_skeleton.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

/// Teacher view of their courses.
class CoursesScreen extends ConsumerStatefulWidget {
  const CoursesScreen({super.key});

  @override
  ConsumerState<CoursesScreen> createState() => _CoursesScreenState();
}

class _CoursesScreenState extends ConsumerState<CoursesScreen> {
  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _items = const [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final res = await ref.read(apiClientProvider).list('/courses');
      if (!mounted) return;
      setState(() => _items = res.data);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('courses.title'))),
      body: _loading
          ? const MobileListSkeleton()
          : _error != null
              ? AppErrorWidget(message: _error!, onRetry: _load)
              : _items.isEmpty
                  ? AppEmptyState(
                      icon: Icons.menu_book_outlined,
                      title: t.t('courses.empty'),
                    )
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _items.length,
                        itemBuilder: (context, index) {
                          final item = _items[index];
                          final description =
                              (item['description'] as String?) ?? '';
                          final status = (item['status'] as String?) ?? '';
                          return Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            child: ListTile(
                              leading: const Icon(Icons.menu_book_outlined),
                              title: Text(item['title']?.toString() ?? ''),
                              subtitle: description.isEmpty
                                  ? null
                                  : Text(description),
                              trailing: status.isEmpty
                                  ? null
                                  : AppBadge(label: status),
                            ),
                          );
                        },
                      ),
                    ),
    );
  }
}
