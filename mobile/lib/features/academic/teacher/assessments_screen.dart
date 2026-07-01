import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/widgets/shimmer_skeleton.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

/// Teacher view of their assessments.
class AssessmentsScreen extends ConsumerStatefulWidget {
  const AssessmentsScreen({super.key});

  @override
  ConsumerState<AssessmentsScreen> createState() => _AssessmentsScreenState();
}

class _AssessmentsScreenState extends ConsumerState<AssessmentsScreen> {
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
      final res = await ref.read(apiClientProvider).list('/assessments');
      if (!mounted) return;
      setState(() => _items = res.data);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _formatDate(String? iso) {
    if (iso == null) return '';
    final parsed = DateTime.tryParse(iso);
    if (parsed == null) return iso;
    return DateFormat.yMMMd().format(parsed.toLocal());
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('assessments.title'))),
      body: _loading
          ? const MobileListSkeleton()
          : _error != null
              ? AppErrorWidget(message: _error!, onRetry: _load)
              : _items.isEmpty
                  ? AppEmptyState(
                      icon: Icons.assignment_turned_in_outlined,
                      title: t.t('assessments.empty'),
                    )
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _items.length,
                        itemBuilder: (context, index) {
                          final item = _items[index];
                          final status = (item['status'] as String?) ?? '';
                          final due = _formatDate(item['due_at'] as String?);
                          final points = item['total_points'];
                          final subtitleParts = [
                            if (due.isNotEmpty) due,
                            if (points != null)
                              '${points.toString()} ${t.t('assignment.points')}',
                          ];
                          return Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            child: ListTile(
                              leading: const Icon(
                                Icons.assignment_turned_in_outlined,
                              ),
                              title: Text(item['title']?.toString() ?? ''),
                              subtitle: subtitleParts.isEmpty
                                  ? null
                                  : Text(subtitleParts.join(' · ')),
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
