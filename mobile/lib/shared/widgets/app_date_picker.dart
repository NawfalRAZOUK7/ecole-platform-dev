import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

class AppDatePicker extends StatelessWidget {
  final DateTime? value;
  final ValueChanged<DateTime> onChanged;
  final String label;

  const AppDatePicker({
    super.key,
    required this.value,
    required this.onChanged,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    final formatted = value == null
        ? null
        : DateFormat.yMMMd('fr_MA').format(value!.toLocal());

    return Semantics(
      button: true,
      label: label,
      value: formatted ?? 'No date selected',
      hint: 'Double tap to choose a date',
      child: ConstrainedBox(
        constraints: const BoxConstraints(minHeight: 48),
        child: InkWell(
          onTap: () => _pickDate(context),
          borderRadius: BorderRadius.circular(12),
          child: InputDecorator(
            decoration: InputDecoration(
              labelText: label,
              suffixIcon: const Icon(Icons.calendar_today_outlined),
            ),
            child: Text(
              formatted ?? label,
              style: formatted == null
                  ? Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      )
                  : null,
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _pickDate(BuildContext context) async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      locale: const Locale('fr', 'MA'),
      initialDate: value ?? now,
      firstDate: DateTime(now.year - 20),
      lastDate: DateTime(now.year + 20),
    );

    if (picked != null) {
      onChanged(picked);
    }
  }
}
