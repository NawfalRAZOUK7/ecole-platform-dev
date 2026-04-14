import 'package:flutter/material.dart';

import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

const List<Color> kidFriendlyColorPalette = <Color>[
  KidsContentColors.gameBlue,
  KidsContentColors.gameGreen,
  KidsContentColors.gamePurple,
  KidsContentColors.gameYellow,
  KidsContentColors.gameRed,
  KidsContentColors.storyPageTurn,
  KidsContentColors.storyHighlight,
  KidsContentColors.samiPrimary,
  KidsContentColors.samiSecondary,
  Color(0xFF8D6E63),
  Colors.black,
  Colors.white,
];

class ColorPickerPalette extends StatelessWidget {
  const ColorPickerPalette({
    super.key,
    required this.selectedColor,
    required this.onColorSelected,
    this.colors = kidFriendlyColorPalette,
    this.swatchSize = 28,
    this.spacing = AppSpacing.sm,
  });

  final List<Color> colors;
  final Color selectedColor;
  final ValueChanged<Color> onColorSelected;
  final double swatchSize;
  final double spacing;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Wrap(
      spacing: spacing,
      runSpacing: spacing,
      children: colors
          .map(
            (color) => _ColorSwatch(
              color: color,
              size: swatchSize,
              selected: selectedColor == color,
              selectedBorderColor: theme.colorScheme.primary,
              onTap: () => onColorSelected(color),
            ),
          )
          .toList(growable: false),
    );
  }
}

class _ColorSwatch extends StatelessWidget {
  const _ColorSwatch({
    required this.color,
    required this.size,
    required this.selected,
    required this.selectedBorderColor,
    required this.onTap,
  });

  final Color color;
  final double size;
  final bool selected;
  final Color selectedBorderColor;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        customBorder: const CircleBorder(),
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 160),
          width: size,
          height: size,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
            border: Border.all(
              color: selected
                  ? selectedBorderColor
                  : KidsContentColors.colorPickerBorder,
              width: selected ? 3 : 1.5,
            ),
            boxShadow: selected
                ? <BoxShadow>[
                    BoxShadow(
                      color: selectedBorderColor.withAlpha(80),
                      blurRadius: 6,
                      offset: const Offset(0, 2),
                    ),
                  ]
                : null,
          ),
          child: color == Colors.white
              ? const Center(
                  child: Icon(
                    Icons.circle_outlined,
                    size: 14,
                    color: KidsContentColors.colorPickerBorder,
                  ),
                )
              : null,
        ),
      ),
    );
  }
}
