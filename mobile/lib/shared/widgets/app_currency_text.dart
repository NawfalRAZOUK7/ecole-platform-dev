import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

class AppCurrencyText extends StatelessWidget {
  final double amount;
  final String currency;
  final TextStyle? style;

  const AppCurrencyText({
    super.key,
    required this.amount,
    this.currency = 'MAD',
    this.style,
  });

  @override
  Widget build(BuildContext context) {
    final formatted = NumberFormat.currency(
      locale: 'fr_MA',
      symbol: currency,
    ).format(amount);

    return Semantics(
      label: formatted,
      child: ExcludeSemantics(
        child: Text(
          formatted,
          style: style ?? Theme.of(context).textTheme.bodyMedium,
        ),
      ),
    );
  }
}
