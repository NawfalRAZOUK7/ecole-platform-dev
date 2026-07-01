part of 'reports_screen.dart';

extension _ReportsGeneratorSection on _ReportsScreenState {
  Widget _buildGeneratorCard(AppLocalizations t) {
    final role = ref.watch(authProvider).user?.role ?? 'STD';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    t.t('reports.generateTitle'),
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                Chip(label: Text(role)),
              ],
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              initialValue: _selectedType,
              decoration:
                  InputDecoration(labelText: t.t('reports.fields.type')),
              items: _availableTypes
                  .map(
                    (item) => DropdownMenuItem(
                      value: item,
                      child: Text(_typeLabel(item, t)),
                    ),
                  )
                  .toList(),
              onChanged: _onTypeChanged,
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _selectedLocale,
              decoration:
                  InputDecoration(labelText: t.t('reports.fields.language')),
              items: const [
                DropdownMenuItem(value: 'fr', child: Text('Français')),
                DropdownMenuItem(value: 'ar', child: Text('العربية')),
                DropdownMenuItem(value: 'en', child: Text('English')),
              ],
              onChanged: (value) {
                if (value != null) {
                  _applyState(() => _selectedLocale = value);
                }
              },
            ),
            if (_options.periods.isNotEmpty) ...[
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _periodId.isEmpty ? null : _periodId,
                decoration:
                    InputDecoration(labelText: t.t('reports.fields.period')),
                items: [
                  DropdownMenuItem(
                    value: '',
                    child: Text(t.t('reports.anyPeriod')),
                  ),
                  ..._options.periods.map(
                    (period) => DropdownMenuItem(
                      value: period.id,
                      child: Text(period.label),
                    ),
                  ),
                ],
                onChanged: (value) {
                  _applyState(() {
                    _periodId = value ?? '';
                  });
                },
              ),
            ],
            if (_needsClass) ...[
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _classId.isEmpty ? null : _classId,
                decoration:
                    InputDecoration(labelText: t.t('reports.fields.class')),
                items: _options.classes
                    .map(
                      (item) => DropdownMenuItem(
                        value: item.id,
                        child: Text(
                          item.secondary == null
                              ? item.label
                              : '${item.label} · ${item.secondary}',
                        ),
                      ),
                    )
                    .toList(),
                onChanged: (value) {
                  _applyState(() => _classId = value ?? '');
                  _load(refresh: false);
                },
              ),
            ],
            if (_needsStudent && _options.students.isNotEmpty) ...[
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _studentId.isEmpty ? null : _studentId,
                decoration:
                    InputDecoration(labelText: t.t('reports.fields.student')),
                items: _options.students
                    .map(
                      (item) => DropdownMenuItem(
                        value: item.id,
                        child: Text(
                          item.secondary == null
                              ? item.label
                              : '${item.label} · ${item.secondary}',
                        ),
                      ),
                    )
                    .toList(),
                onChanged: (value) {
                  _applyState(() => _studentId = value ?? '');
                },
              ),
            ],
            if (_needsParent && _options.parents.isNotEmpty) ...[
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _parentId.isEmpty ? null : _parentId,
                decoration:
                    InputDecoration(labelText: t.t('reports.fields.parent')),
                items: _options.parents
                    .map(
                      (item) => DropdownMenuItem(
                        value: item.id,
                        child: Text(
                          item.secondary == null
                              ? item.label
                              : '${item.label} · ${item.secondary}',
                        ),
                      ),
                    )
                    .toList(),
                onChanged: (value) {
                  _applyState(() => _parentId = value ?? '');
                },
              ),
            ],
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _DateTile(
                    label: t.t('reports.fields.from'),
                    value: _displayDate(_fromDate, t.locale),
                    onTap:
                        _periodId.isEmpty ? () => _pickDate(from: true) : null,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _DateTile(
                    label: t.t('reports.fields.to'),
                    value: _displayDate(_toDate, t.locale),
                    onTap:
                        _periodId.isEmpty ? () => _pickDate(from: false) : null,
                  ),
                ),
              ],
            ),
            if (_selectedType == 'school_analytics') ...[
              const SizedBox(height: 12),
              SwitchListTile(
                value: _compare,
                contentPadding: EdgeInsets.zero,
                title: Text(t.t('reports.comparePrevious')),
                onChanged: (value) {
                  _applyState(() => _compare = value);
                },
              ),
            ],
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _submitting ? null : _generateReport,
                icon: _submitting
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.picture_as_pdf_outlined),
                label: Text(
                  _submitting
                      ? t.t('reports.generating')
                      : t.t('reports.generate'),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _typeLabel(String type, AppLocalizations t) {
    return t.t('reports.types.$type');
  }

  String _statusLabel(String status, AppLocalizations t) {
    return t.t('reports.status.$status');
  }

  String _describeScope(ReportJob job, AppLocalizations t) {
    final parameters = job.parameters;
    if (parameters['period_label'] != null) {
      return parameters['period_label'].toString();
    }
    if (parameters['from_date'] != null && parameters['to_date'] != null) {
      return '${parameters['from_date']} → ${parameters['to_date']}';
    }
    if (parameters['student_id'] != null) {
      return '${t.t('reports.fields.student')}: ${parameters['student_id']}';
    }
    if (parameters['class_id'] != null) {
      return '${t.t('reports.fields.class')}: ${parameters['class_id']}';
    }
    if (parameters['parent_id'] != null) {
      return '${t.t('reports.fields.parent')}: ${parameters['parent_id']}';
    }
    return t.t('reports.scopeDefault');
  }

  String _displayDate(DateTime? value, String locale) {
    if (value == null) return '—';
    return DateFormat.yMMMd(locale).format(value);
  }

  String _formatDateTime(String value, String locale) {
    try {
      return DateFormat.yMMMd(locale)
          .add_Hm()
          .format(DateTime.parse(value).toLocal());
    } catch (_) {
      return value;
    }
  }

  String? _formatDateParam(DateTime? value) {
    if (value == null) return null;
    return DateFormat('yyyy-MM-dd').format(value);
  }

  Map<String, dynamic> _currentScheduleParameters() {
    return {
      'locale': _selectedLocale,
      if (_periodId.isNotEmpty) 'period_id': _periodId,
      if (_classId.isNotEmpty) 'class_id': _classId,
      if (_studentId.isNotEmpty) 'student_id': _studentId,
      if (_parentId.isNotEmpty) 'parent_id': _parentId,
      if (_formatDateParam(_fromDate) != null)
        'from_date': _formatDateParam(_fromDate),
      if (_formatDateParam(_toDate) != null)
        'to_date': _formatDateParam(_toDate),
      'compare': _compare,
    };
  }
}

class _DateTile extends StatelessWidget {
  final String label;
  final String value;
  final VoidCallback? onTap;

  const _DateTile({
    required this.label,
    required this.value,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: InputDecorator(
        decoration: InputDecoration(
          labelText: label,
          enabled: onTap != null,
        ),
        child: Row(
          children: [
            Expanded(child: Text(value)),
            const Icon(Icons.calendar_today_outlined, size: 18),
          ],
        ),
      ),
    );
  }
}
