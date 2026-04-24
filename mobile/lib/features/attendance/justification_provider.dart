library;

import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/child_link.dart';

class ChildAbsence {
  final String recordId;
  final String studentId;
  final String sessionDate;
  final String slot;
  final String? absenceReason;
  final String? justificationStatus;

  const ChildAbsence({
    required this.recordId,
    required this.studentId,
    required this.sessionDate,
    required this.slot,
    this.absenceReason,
    this.justificationStatus,
  });

  factory ChildAbsence.fromJson(Map<String, dynamic> json) => ChildAbsence(
        recordId: json['id'] as String? ?? '',
        studentId: json['student_id'] as String? ?? '',
        sessionDate: json['session_date'] as String? ?? '',
        slot: json['slot'] as String? ?? '',
        absenceReason: json['absence_reason'] as String?,
        justificationStatus: json['justification_status'] as String?,
      );
}

class SubmittedJustification {
  final String id;
  final String attendanceRecordId;
  final String status;
  final String? reason;
  final String? rejectionReason;
  final String? attachmentUrl;
  final String? sessionDate;
  final String? studentId;
  final String? createdAt;

  const SubmittedJustification({
    required this.id,
    required this.attendanceRecordId,
    required this.status,
    this.reason,
    this.rejectionReason,
    this.attachmentUrl,
    this.sessionDate,
    this.studentId,
    this.createdAt,
  });

  factory SubmittedJustification.fromJson(Map<String, dynamic> json) =>
      SubmittedJustification(
        id: json['id'] as String? ?? '',
        attendanceRecordId: json['attendance_record_id'] as String? ?? '',
        status: json['status'] as String? ?? 'pending',
        reason: json['reason'] as String?,
        rejectionReason: json['rejection_reason'] as String?,
        attachmentUrl: json['attachment_url'] as String?,
        sessionDate: json['session_date'] as String?,
        studentId: json['student_id'] as String?,
        createdAt: json['created_at'] as String?,
      );
}

class JustificationData {
  final List<ChildLink> children;
  final Map<String, List<ChildAbsence>> absencesByChild;
  final List<SubmittedJustification> submitted;

  const JustificationData({
    required this.children,
    required this.absencesByChild,
    required this.submitted,
  });

  JustificationData copyWith({
    List<ChildLink>? children,
    Map<String, List<ChildAbsence>>? absencesByChild,
    List<SubmittedJustification>? submitted,
  }) =>
      JustificationData(
        children: children ?? this.children,
        absencesByChild: absencesByChild ?? this.absencesByChild,
        submitted: submitted ?? this.submitted,
      );
}

class JustificationNotifier extends AsyncNotifier<JustificationData> {
  @override
  Future<JustificationData> build() async {
    return _load();
  }

  Future<JustificationData> _load() async {
    final api = ref.read(apiClientProvider);
    final authRepo = ref.read(authRepositoryProvider);

    final children = await authRepo.getChildren();

    final absencesByChild = <String, List<ChildAbsence>>{};
    for (final child in children) {
      final resp = await api.list(
        '/attendance/records/student/${child.userId}',
        params: <String, dynamic>{'status': 'absent'},
      );
      absencesByChild[child.userId] =
          resp.data.map(ChildAbsence.fromJson).toList();
    }

    final mineResp = await api.list('/attendance/justifications/mine');
    final submitted =
        mineResp.data.map(SubmittedJustification.fromJson).toList();

    return JustificationData(
      children: children,
      absencesByChild: absencesByChild,
      submitted: submitted,
    );
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_load);
  }

  Future<void> submit({
    required String attendanceRecordId,
    required String reason,
    File? attachment,
  }) async {
    final api = ref.read(apiClientProvider);
    final fields = <String, dynamic>{
      'attendance_record_id': attendanceRecordId,
      'reason': reason,
    };
    if (attachment != null) {
      await api.uploadFile(
        '/attendance/justifications',
        file: attachment,
        fileField: 'attachment',
        fields: fields,
      );
    } else {
      final formData = FormData.fromMap(fields);
      await api.post('/attendance/justifications', body: formData);
    }
    await refresh();
  }
}

final justificationProvider =
    AsyncNotifierProvider<JustificationNotifier, JustificationData>(
  JustificationNotifier.new,
);
