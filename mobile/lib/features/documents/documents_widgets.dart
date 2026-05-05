part of 'documents_screen.dart';

class _DocumentCard extends StatelessWidget {
  final ManagedDocument item;
  final String locale;
  final VoidCallback onTap;
  final VoidCallback onShare;
  final VoidCallback? onDelete;

  const _DocumentCard({
    required this.item,
    required this.locale,
    required this.onTap,
    required this.onShare,
    this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations(locale);
    final createdAt = _formatDate(item.createdAt, locale);
    final expiresAt =
        item.expiresAt == null ? null : _formatDate(item.expiresAt!, locale);
    final theme = Theme.of(context);

    return Card(
      child: ListTile(
        onTap: onTap,
        leading: _DocumentThumb(item: item),
        title: Text(
          item.originalFilename,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                _MetaChip(label: t.t('documents.categories.${item.category}')),
                _MetaChip(label: _humanSize(item.sizeBytes)),
                if (item.availableOffline)
                  _MetaChip(label: t.t('documents.offline')),
                if (item.deduplicated) const _MetaChip(label: 'SHA-256'),
                if (item.isExpired)
                  _MetaChip(
                    label: t.t('documents.status.expired'),
                    color: theme.colorScheme.error,
                  ),
                if (item.isExpiringSoon)
                  _MetaChip(
                    label: t.t('documents.expiring'),
                    color: theme.semanticPalette.warning,
                  ),
              ],
            ),
            const SizedBox(height: 6),
            Text(createdAt),
            if (item.linkedStudentName != null &&
                item.linkedStudentName!.isNotEmpty)
              Text(item.linkedStudentName!),
            if (expiresAt != null) Text(expiresAt),
          ],
        ),
        trailing: PopupMenuButton<String>(
          onSelected: (value) {
            switch (value) {
              case 'share':
                onShare();
                break;
              case 'delete':
                onDelete?.call();
                break;
            }
          },
          itemBuilder: (context) => [
            PopupMenuItem(
              value: 'share',
              child: Text(t.t('documents.share')),
            ),
            if (onDelete != null)
              PopupMenuItem(
                value: 'delete',
                child: Text(t.t('documents.delete')),
              ),
          ],
        ),
      ),
    );
  }
}

class _ChecklistCard extends StatelessWidget {
  final StudentDocumentChecklistItem item;
  final String locale;

  const _ChecklistCard({
    required this.item,
    required this.locale,
  });

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations(locale);
    final theme = Theme.of(context);
    final color = switch (item.status) {
      'uploaded' => theme.semanticPalette.success,
      'expired' => theme.colorScheme.error,
      _ => theme.semanticPalette.warning,
    };
    final expiresLabel =
        item.expiresAt == null ? null : _formatDate(item.expiresAt!, locale);

    return Card(
      child: ListTile(
        title: Text(t.t('documents.categories.${item.category}')),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (item.description != null && item.description!.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(item.description!),
              ),
            if (item.document != null)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(item.document!.originalFilename),
              ),
            if (expiresLabel != null)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(expiresLabel),
              ),
          ],
        ),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.14),
            borderRadius: BorderRadius.circular(999),
          ),
          child: Text(
            t.t('documents.status.${item.status}'),
            style: TextStyle(color: color, fontWeight: FontWeight.w600),
          ),
        ),
      ),
    );
  }
}

class _ResourceCard extends StatelessWidget {
  final ResourceLibraryItem item;
  final String locale;
  final VoidCallback onTap;
  final VoidCallback onDownload;
  final VoidCallback? onRate;
  final VoidCallback? onDelete;

  const _ResourceCard({
    required this.item,
    required this.locale,
    required this.onTap,
    required this.onDownload,
    this.onRate,
    this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations(locale);
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item.title,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 6),
                        Wrap(
                          spacing: 6,
                          runSpacing: 6,
                          children: [
                            if (item.subject != null &&
                                item.subject!.isNotEmpty)
                              _MetaChip(label: item.subject!),
                            if (item.level != null && item.level!.isNotEmpty)
                              _MetaChip(label: item.level!),
                            _MetaChip(
                              label:
                                  t.t('documents.resourceTypes.${item.type}'),
                            ),
                            if (item.availableOffline)
                              _MetaChip(label: t.t('documents.offline')),
                          ],
                        ),
                      ],
                    ),
                  ),
                  if (onDelete != null)
                    IconButton(
                      onPressed: onDelete,
                      icon: const Icon(Icons.delete_outline),
                    ),
                ],
              ),
              if (item.description != null && item.description!.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(item.description!),
              ],
              const SizedBox(height: 12),
              Row(
                children: [
                  ...List.generate(
                    5,
                    (index) => Icon(
                      index < item.avgRating.round()
                          ? Icons.star
                          : Icons.star_border,
                      size: 18,
                      color: Theme.of(context).semanticPalette.warning,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '${item.avgRating.toStringAsFixed(1)} · ${item.ratingCount}',
                  ),
                  const Spacer(),
                  Text('${item.downloadCount}'),
                ],
              ),
              if (item.tags.isNotEmpty) ...[
                const SizedBox(height: 12),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: item.tags
                      .take(4)
                      .map((tag) => _MetaChip(label: '#$tag'))
                      .toList(),
                ),
              ],
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  OutlinedButton.icon(
                    onPressed: onTap,
                    icon: const Icon(Icons.visibility_outlined),
                    label: Text(t.t('documents.preview')),
                  ),
                  OutlinedButton.icon(
                    onPressed: onDownload,
                    icon: const Icon(Icons.download_outlined),
                    label: Text(t.t('documents.download')),
                  ),
                  if (onRate != null)
                    OutlinedButton.icon(
                      onPressed: onRate,
                      icon: const Icon(Icons.star_outline),
                      label: Text(t.t('documents.rate')),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DocumentThumb extends StatelessWidget {
  final ManagedDocument item;

  const _DocumentThumb({required this.item});

  @override
  Widget build(BuildContext context) {
    if (item.isImage &&
        item.thumbnailUrl != null &&
        item.thumbnailUrl!.isNotEmpty) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(10),
        child: SignedNetworkImage(
          path: item.thumbnailUrl!,
          width: 52,
          height: 52,
          fit: BoxFit.cover,
          errorBuilder: (context, error, stackTrace) {
            return _fallback(context);
          },
        ),
      );
    }
    return _fallback(context);
  }

  Widget _fallback(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      width: 52,
      height: 52,
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(10),
      ),
      alignment: Alignment.center,
      child: Icon(
        item.isPdf
            ? Icons.picture_as_pdf_outlined
            : item.isImage
                ? Icons.image_outlined
                : Icons.insert_drive_file_outlined,
      ),
    );
  }
}

class _MetaChip extends StatelessWidget {
  final String label;
  final Color? color;

  const _MetaChip({
    required this.label,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final foreground = color ?? theme.colorScheme.onSurfaceVariant;
    final background = color == null
        ? theme.colorScheme.surfaceContainerHighest
        : color!.withValues(alpha: 0.12);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: foreground,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class _CategoryChipBar extends StatelessWidget {
  final List<String> categories;
  final String selected;
  final ValueChanged<String> onChanged;

  const _CategoryChipBar({
    required this.categories,
    required this.selected,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations(Localizations.localeOf(context).languageCode);
    final allCategories = categories.isEmpty ? const ['other'] : categories;
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        ChoiceChip(
          label: Text(t.t('documents.all')),
          selected: selected.isEmpty,
          onSelected: (_) => onChanged(''),
        ),
        ...allCategories.map(
          (category) => ChoiceChip(
            label: Text(t.t('documents.categories.$category')),
            selected: selected == category,
            onSelected: (_) => onChanged(category),
          ),
        ),
      ],
    );
  }
}

class _ErrorCard extends StatelessWidget {
  final String message;

  const _ErrorCard({required this.message});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      color: theme.colorScheme.errorContainer,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Text(
          message,
          style: TextStyle(color: theme.colorScheme.onErrorContainer),
        ),
      ),
    );
  }
}

class _UploadProgressCard extends StatelessWidget {
  final String title;
  final double progress;

  const _UploadProgressCard({
    required this.title,
    required this.progress,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title),
            const SizedBox(height: 8),
            LinearProgressIndicator(value: progress.clamp(0, 1)),
            const SizedBox(height: 8),
            Text('${(progress * 100).round()}%'),
          ],
        ),
      ),
    );
  }
}

String _humanSize(int bytes) {
  if (bytes < 1024) return '$bytes B';
  if (bytes < 1024 * 1024) {
    return '${(bytes / 1024).toStringAsFixed(1)} KB';
  }
  return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
}

String _formatDate(String value, String locale) {
  try {
    final parsed = DateTime.parse(value).toLocal();
    return DateFormat.yMMMd(locale).add_Hm().format(parsed);
  } catch (_) {
    return value;
  }
}
