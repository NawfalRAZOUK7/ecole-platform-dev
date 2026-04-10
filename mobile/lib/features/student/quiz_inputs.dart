part of 'quiz_player_screen.dart';

class _McqInput extends StatelessWidget {
  final Question question;
  final String? answer;
  final ValueChanged<String> onChanged;

  const _McqInput({
    required this.question,
    this.answer,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final choices = question.options?['choices'] as List<dynamic>? ?? [];

    return Column(
      children: choices.map((choice) {
        final label = choice is Map
            ? (choice['label'] ?? choice['text'] ?? '') as String
            : choice.toString();
        final value = choice is Map
            ? (choice['value'] ?? choice['key'] ?? label) as String
            : choice.toString();
        final selected = answer == value;

        return GestureDetector(
          onTap: () => onChanged(value),
          child: Container(
            width: double.infinity,
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: selected
                  ? theme.colorScheme.primaryContainer
                  : theme.colorScheme.surface,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: selected
                    ? theme.colorScheme.primary
                    : theme.colorScheme.outline,
                width: selected ? 2 : 1,
              ),
            ),
            child: Row(
              children: [
                Icon(
                  selected
                      ? Icons.radio_button_checked
                      : Icons.radio_button_off,
                  color: selected ? theme.colorScheme.primary : Colors.grey,
                  size: 22,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(label, style: const TextStyle(fontSize: 15)),
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}

class _TrueFalseInput extends StatelessWidget {
  final bool? answer;
  final ValueChanged<bool> onChanged;

  const _TrueFalseInput({
    this.answer,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _toggleCard(context, true, 'Vrai', Icons.check_circle_outline),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: _toggleCard(context, false, 'Faux', Icons.cancel_outlined),
        ),
      ],
    );
  }

  Widget _toggleCard(
    BuildContext context,
    bool value,
    String label,
    IconData icon,
  ) {
    final theme = Theme.of(context);
    final selected = answer == value;

    return GestureDetector(
      onTap: () => onChanged(value),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 32),
        decoration: BoxDecoration(
          color: selected
              ? (value ? Colors.green.withAlpha(25) : Colors.red.withAlpha(25))
              : theme.colorScheme.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: selected
                ? (value ? Colors.green : Colors.red)
                : theme.colorScheme.outline,
            width: selected ? 2 : 1,
          ),
        ),
        child: Column(
          children: [
            Icon(
              icon,
              size: 40,
              color:
                  selected ? (value ? Colors.green : Colors.red) : Colors.grey,
            ),
            const SizedBox(height: 8),
            Text(
              label,
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: selected
                    ? (value ? Colors.green : Colors.red)
                    : Colors.grey,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FillInInput extends StatelessWidget {
  final String answer;
  final ValueChanged<String> onChanged;

  const _FillInInput({
    required this.answer,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      initialValue: answer,
      onChanged: onChanged,
      decoration: const InputDecoration(
        labelText: 'Votre réponse',
        hintText: 'Tapez votre réponse ici...',
        border: OutlineInputBorder(),
      ),
      maxLines: 3,
    );
  }
}

class _DragDropInput extends StatelessWidget {
  final Question question;
  final Map<String, String> answers;
  final ValueChanged<Map<String, String>> onChanged;

  const _DragDropInput({
    required this.question,
    required this.answers,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final zones = question.options?['zones'] as List<dynamic>? ?? [];
    final items = question.options?['items'] as List<dynamic>? ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Faites glisser les éléments vers les zones :',
          style: theme.textTheme.bodySmall,
        ),
        const SizedBox(height: 12),
        ...zones.map((zone) {
          final zoneName = zone is Map
              ? (zone['label'] ?? zone['id'] ?? '') as String
              : zone.toString();
          final zoneId = zone is Map
              ? (zone['id'] ?? zone['label'] ?? '') as String
              : zone.toString();

          return Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Row(
              children: [
                Expanded(
                  flex: 2,
                  child: Text(
                    zoneName,
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  flex: 3,
                  child: DropdownButtonFormField<String>(
                    initialValue: answers[zoneId],
                    decoration: InputDecoration(
                      border: const OutlineInputBorder(),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 8,
                      ),
                      hintText: 'Sélectionner...',
                      fillColor: theme.colorScheme.surface,
                    ),
                    items: items.map((item) {
                      final label = item is Map
                          ? (item['label'] ?? item['text'] ?? '') as String
                          : item.toString();
                      return DropdownMenuItem(
                        value: label,
                        child: Text(
                          label,
                          style: const TextStyle(fontSize: 13),
                        ),
                      );
                    }).toList(),
                    onChanged: (value) {
                      if (value != null) {
                        final updated = Map<String, String>.from(answers);
                        updated[zoneId] = value;
                        onChanged(updated);
                      }
                    },
                  ),
                ),
              ],
            ),
          );
        }),
      ],
    );
  }
}

class _MatchingInput extends StatelessWidget {
  final Question question;
  final Map<String, String> answers;
  final ValueChanged<Map<String, String>> onChanged;

  const _MatchingInput({
    required this.question,
    required this.answers,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final leftItems = question.options?['left'] as List<dynamic>? ?? [];
    final rightItems = question.options?['right'] as List<dynamic>? ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Associez chaque élément de gauche avec celui de droite :',
          style: theme.textTheme.bodySmall,
        ),
        const SizedBox(height: 12),
        ...leftItems.map((left) {
          final leftLabel = left is Map
              ? (left['label'] ?? left['text'] ?? '') as String
              : left.toString();
          final leftId = left is Map
              ? (left['id'] ?? left['label'] ?? '') as String
              : left.toString();

          return Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Row(
              children: [
                Expanded(
                  flex: 2,
                  child: Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primaryContainer,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      leftLabel,
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ),
                ),
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 8),
                  child:
                      Icon(Icons.arrow_forward, size: 18, color: Colors.grey),
                ),
                Expanded(
                  flex: 3,
                  child: DropdownButtonFormField<String>(
                    initialValue: answers[leftId],
                    decoration: const InputDecoration(
                      border: OutlineInputBorder(),
                      contentPadding:
                          EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      hintText: 'Sélectionner...',
                    ),
                    items: rightItems.map((right) {
                      final label = right is Map
                          ? (right['label'] ?? right['text'] ?? '') as String
                          : right.toString();
                      return DropdownMenuItem(
                        value: label,
                        child: Text(
                          label,
                          style: const TextStyle(fontSize: 13),
                        ),
                      );
                    }).toList(),
                    onChanged: (value) {
                      if (value != null) {
                        final updated = Map<String, String>.from(answers);
                        updated[leftId] = value;
                        onChanged(updated);
                      }
                    },
                  ),
                ),
              ],
            ),
          );
        }),
      ],
    );
  }
}
