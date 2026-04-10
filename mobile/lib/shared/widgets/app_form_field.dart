import 'package:flutter/material.dart';

class AppFormField extends StatelessWidget {
  final TextEditingController controller;
  final String label;
  final String? hint;
  final String? Function(String?)? validator;
  final TextInputType? keyboardType;
  final bool obscure;
  final TextInputAction? textInputAction;
  final int? maxLines;

  const AppFormField({
    super.key,
    required this.controller,
    required this.label,
    this.hint,
    this.validator,
    this.keyboardType,
    this.obscure = false,
    this.textInputAction,
    this.maxLines = 1,
  });

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      validator: validator,
      keyboardType: keyboardType,
      obscureText: obscure,
      textInputAction: textInputAction,
      maxLines: obscure ? 1 : maxLines,
      autovalidateMode: AutovalidateMode.onUserInteraction,
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
      ),
    );
  }
}
