/// Biometric authentication service — fingerprint / FaceID unlock.
///
/// Reference: Phase 5A — Biometric auth
/// - Check device capability (fingerprint / face)
/// - Authenticate with biometric
/// - Fallback to password after 3 failures
/// - Store biometric preference in secure storage

import 'dart:developer' as dev;

import 'package:flutter/services.dart';
import 'package:local_auth/local_auth.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

const String _biometricEnabledKey = 'ecole_biometric_enabled';
const int maxBiometricAttempts = 3;

class BiometricService {
  final LocalAuthentication _auth = LocalAuthentication();
  final FlutterSecureStorage _storage = const FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
    iOptions: IOSOptions(
      accessibility: KeychainAccessibility.first_unlock_this_device,
    ),
  );

  int _failedAttempts = 0;

  /// Check if device supports biometric authentication.
  Future<bool> isAvailable() async {
    try {
      final canCheck = await _auth.canCheckBiometrics;
      final isSupported = await _auth.isDeviceSupported();
      return canCheck && isSupported;
    } on PlatformException catch (e) {
      dev.log('Biometric availability check failed: $e',
          name: 'BiometricService');
      return false;
    }
  }

  /// Get available biometric types (fingerprint, face, iris).
  Future<List<BiometricType>> getAvailableTypes() async {
    try {
      return await _auth.getAvailableBiometrics();
    } on PlatformException {
      return [];
    }
  }

  /// Check if user has enabled biometric unlock.
  Future<bool> isEnabled() async {
    final value = await _storage.read(key: _biometricEnabledKey);
    return value == 'true';
  }

  /// Enable or disable biometric unlock.
  Future<void> setEnabled(bool enabled) async {
    await _storage.write(
      key: _biometricEnabledKey,
      value: enabled ? 'true' : 'false',
    );
  }

  /// Whether fallback to password is required (3 failures reached).
  bool get shouldFallbackToPassword => _failedAttempts >= maxBiometricAttempts;

  /// Reset the failure counter (e.g. after successful password login).
  void resetAttempts() => _failedAttempts = 0;

  /// Authenticate with biometric. Returns true on success.
  /// Increments failure counter on failure.
  Future<bool> authenticate({String reason = 'Veuillez vous authentifier'}) async {
    if (shouldFallbackToPassword) return false;

    try {
      final success = await _auth.authenticate(
        localizedReason: reason,
        options: const AuthenticationOptions(
          stickyAuth: true,
          biometricOnly: true,
        ),
      );

      if (success) {
        _failedAttempts = 0;
        dev.log('Biometric auth succeeded', name: 'BiometricService');
      } else {
        _failedAttempts++;
        dev.log(
          'Biometric auth failed (attempt $_failedAttempts/$maxBiometricAttempts)',
          name: 'BiometricService',
        );
      }

      return success;
    } on PlatformException catch (e) {
      _failedAttempts++;
      dev.log('Biometric auth error: $e (attempt $_failedAttempts)',
          name: 'BiometricService');
      return false;
    }
  }

  /// Clear stored biometric preference (on logout).
  Future<void> clear() async {
    await _storage.delete(key: _biometricEnabledKey);
    _failedAttempts = 0;
  }
}
