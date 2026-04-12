import 'package:ecole_platform/data/api/api_client.dart';

ApiResponse<Map<String, dynamic>> response(Map<String, dynamic> data) {
  return ApiResponse<Map<String, dynamic>>(data: data);
}

ApiListResponse<Map<String, dynamic>> listResponse(
  List<Map<String, dynamic>> data, {
  String? nextCursor,
  bool hasMore = false,
}) {
  return ApiListResponse<Map<String, dynamic>>(
    data: data,
    nextCursor: nextCursor,
    hasMore: hasMore,
  );
}

ApiClientError offlineError([String message = 'Offline']) {
  return ApiClientError(
    503,
    ApiError(
      code: 'ERR-OFFLINE',
      message: message,
      category: 'network',
      retryable: true,
    ),
  );
}
