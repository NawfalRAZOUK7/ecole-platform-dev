import 'dart:io';

import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/domain/entities/reports/financial_health.dart';
import 'package:ecole_platform/domain/repositories/reports/financial_health_repository.dart';
import 'package:path_provider/path_provider.dart';

class FinancialHealthRepositoryImpl implements FinancialHealthRepository {
  final ApiClient _api;

  FinancialHealthRepositoryImpl({required ApiClient api}) : _api = api;

  @override
  Future<List<RetentionMetric>> listRetentionMetrics({
    Map<String, dynamic>? params,
  }) async {
    final response =
        await _api.list('/financial-health/retention', params: params);
    return response.data.map(RetentionMetric.fromJson).toList();
  }

  @override
  Future<RetentionMetric> computeRetention(Map<String, dynamic> payload) async {
    final response =
        await _api.post('/financial-health/retention/compute', body: payload);
    return RetentionMetric.fromJson(response.data);
  }

  @override
  Future<List<CashflowForecast>> listCashflowForecasts({
    Map<String, dynamic>? params,
  }) async {
    final response =
        await _api.list('/financial-health/cashflow', params: params);
    return response.data.map(CashflowForecast.fromJson).toList();
  }

  @override
  Future<List<CashflowForecast>> computeCashflow(
    Map<String, dynamic> payload,
  ) async {
    final response = await _api.postList(
      '/financial-health/cashflow/compute',
      body: payload,
    );
    return response.data.map(CashflowForecast.fromJson).toList();
  }

  @override
  Future<CostPerStudentAnalysis> getCostPerStudent(
    String academicYearId,
  ) async {
    final response = await _api.get(
      '/financial-health/cost-per-student',
      params: {'academic_year_id': academicYearId},
    );
    return CostPerStudentAnalysis.fromJson(response.data);
  }

  @override
  Future<CostPerStudentAnalysis> computeCostPerStudent(
    Map<String, dynamic> payload,
  ) async {
    final response = await _api.post(
      '/financial-health/cost-per-student/compute',
      body: payload,
    );
    return CostPerStudentAnalysis.fromJson(response.data);
  }

  @override
  Future<FinancialSnapshot> getSnapshot({String? snapshotDate}) async {
    final response = await _api.get(
      '/financial-health/snapshot',
      params: {
        if (snapshotDate != null) 'snapshot_date': snapshotDate,
      },
    );
    return FinancialSnapshot.fromJson(response.data);
  }

  @override
  Future<FinancialSnapshot> computeSnapshot(
    Map<String, dynamic> payload,
  ) async {
    final response =
        await _api.post('/financial-health/snapshot/compute', body: payload);
    return FinancialSnapshot.fromJson(response.data);
  }

  @override
  Future<FinancialHealthDashboard> getDashboard() async {
    final response = await _api.get('/financial-health/dashboard');
    return FinancialHealthDashboard.fromJson(response.data);
  }

  @override
  Future<List<Map<String, dynamic>>> getTrends({int months = 12}) async {
    final response = await _api.get(
      '/financial-health/trends',
      params: {'months': months},
    );
    final data = response.data['series'] as List<dynamic>? ??
        response.data['data'] as List<dynamic>? ??
        const [];
    return data.cast<Map<String, dynamic>>();
  }

  @override
  Future<File> exportCsv() async {
    final directory = await getTemporaryDirectory();
    final path = '${directory.path}/financial-health.csv';
    return _api.download('/financial-health/export/csv', savePath: path);
  }

  @override
  Future<File> exportPdf() async {
    final directory = await getTemporaryDirectory();
    final path = '${directory.path}/financial-health.pdf';
    return _api.download('/financial-health/export/pdf', savePath: path);
  }
}
