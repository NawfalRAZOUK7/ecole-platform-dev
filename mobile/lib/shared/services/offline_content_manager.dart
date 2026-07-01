/// Offline content manager — download and cache content items for offline use.
///
/// Downloads content item metadata (7-day TTL) and asset files (30-day TTL)
/// to the app documents directory so kids in low-connectivity areas can still
/// read stories and view coloring pages.
///
/// Manifest stored at: `<documents>/offline/manifest.json`
/// Assets stored at:   `<documents>/offline/<contentItemId>/<assetId>`

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:path_provider/path_provider.dart';

import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/core/storage/cache_store.dart';
import 'package:ecole_platform/core/network/signed_url_cache.dart';

// ── Download status ───────────────────────────────────────────────────────────

enum DownloadStatus { idle, downloading, done, error }

class DownloadState {
  final DownloadStatus status;
  final double progress; // 0.0–1.0
  final String? error;

  const DownloadState({
    this.status = DownloadStatus.idle,
    this.progress = 0,
    this.error,
  });

  bool get isDownloading => status == DownloadStatus.downloading;
  bool get isDone => status == DownloadStatus.done;
}

// ── Manager ───────────────────────────────────────────────────────────────────

class OfflineContentManager {
  final ApiClient _api;
  final CacheStore _cache;
  final SignedUrlCache _signedUrls;

  /// Live download states keyed by contentItemId.
  final _downloadStates =
      StreamController<Map<String, DownloadState>>.broadcast();
  final Map<String, DownloadState> _states = {};

  Stream<Map<String, DownloadState>> get downloadStatesStream =>
      _downloadStates.stream;

  OfflineContentManager({
    required ApiClient api,
    required CacheStore cache,
    SignedUrlCache? signedUrls,
  })  : _api = api,
        _cache = cache,
        _signedUrls = signedUrls ?? SignedUrlCache(api: api);

  // ── Filesystem helpers ─────────────────────────────────────────────────────

  Future<Directory> _offlineDir() async {
    final docs = await getApplicationDocumentsDirectory();
    final dir = Directory('${docs.path}/offline');
    if (!await dir.exists()) await dir.create(recursive: true);
    return dir;
  }

  Future<File> _manifestFile() async {
    final dir = await _offlineDir();
    return File('${dir.path}/manifest.json');
  }

  // ── Manifest ───────────────────────────────────────────────────────────────

  Future<Map<String, List<String>>> _readManifest() async {
    final file = await _manifestFile();
    if (!await file.exists()) return {};
    try {
      final raw = await file.readAsString();
      final decoded = jsonDecode(raw) as Map<String, dynamic>;
      return decoded.map(
        (k, v) => MapEntry(k, (v as List<dynamic>).cast<String>()),
      );
    } catch (_) {
      return {};
    }
  }

  Future<void> _writeManifest(Map<String, List<String>> manifest) async {
    final file = await _manifestFile();
    await file.writeAsString(jsonEncode(manifest));
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  /// Download content item metadata + all assets for offline use.
  Future<void> downloadForOffline(String contentItemId) async {
    if (_states[contentItemId]?.isDownloading ?? false) return;

    _updateState(
      contentItemId,
      const DownloadState(status: DownloadStatus.downloading),
    );

    try {
      // 1. Fetch and cache metadata with long TTL
      final metaResp = await _api.get('/content-items/$contentItemId');
      await _cache.put(
        'offline:content:$contentItemId',
        <Map<String, dynamic>>[metaResp.data],
        CacheTtl.offlineContent,
      );

      // 2. Fetch asset list
      final assetsResp =
          await _api.list('/content-items/$contentItemId/assets');
      final assets = assetsResp.data;

      // 3. Download each asset to local storage
      final dir = await _offlineDir();
      final contentDir = Directory('${dir.path}/$contentItemId');
      if (!await contentDir.exists()) await contentDir.create(recursive: true);

      final assetIds = <String>[];
      for (var i = 0; i < assets.length; i++) {
        final asset = assets[i];
        final assetId = asset['id'] as String? ?? '';
        if (assetId.isEmpty) continue;

        final savePath = '${contentDir.path}/$assetId';
        await _signedUrls.download(
          '/content-items/$contentItemId/assets/$assetId',
          savePath: savePath,
        );
        assetIds.add(assetId);

        // Update progress
        _updateState(
          contentItemId,
          DownloadState(
            status: DownloadStatus.downloading,
            progress: (i + 1) / assets.length,
          ),
        );
      }

      // 4. Update manifest
      final manifest = await _readManifest();
      manifest[contentItemId] = assetIds;
      await _writeManifest(manifest);

      _updateState(
        contentItemId,
        const DownloadState(status: DownloadStatus.done, progress: 1),
      );
    } catch (e) {
      _updateState(
        contentItemId,
        DownloadState(status: DownloadStatus.error, error: e.toString()),
      );
    }
  }

  /// Returns true if the content item is available offline.
  Future<bool> isAvailableOffline(String contentItemId) async {
    final manifest = await _readManifest();
    return manifest.containsKey(contentItemId);
  }

  /// Returns cached metadata for offline content, or null if not available.
  Future<Map<String, dynamic>?> getOfflineContent(String contentItemId) async {
    final cached = await _cache.get('offline:content:$contentItemId');
    if (cached == null || cached.isEmpty) return null;
    return cached.first;
  }

  /// Returns the local file path for a downloaded asset, or null if missing.
  Future<String?> getOfflineAssetPath(
    String contentItemId,
    String assetId,
  ) async {
    final dir = await _offlineDir();
    final file = File('${dir.path}/$contentItemId/$assetId');
    if (await file.exists()) return file.path;
    return null;
  }

  /// Removes all downloaded files and cache entries for a content item.
  Future<void> removeOfflineContent(String contentItemId) async {
    // Delete local files
    final dir = await _offlineDir();
    final contentDir = Directory('${dir.path}/$contentItemId');
    if (await contentDir.exists()) await contentDir.delete(recursive: true);

    // Remove from cache
    await _cache.invalidate('offline:content:$contentItemId');

    // Update manifest
    final manifest = await _readManifest();
    manifest.remove(contentItemId);
    await _writeManifest(manifest);

    _updateState(contentItemId, const DownloadState());
  }

  /// Returns list of all downloaded content item IDs.
  Future<List<String>> getOfflineContentIds() async {
    final manifest = await _readManifest();
    return manifest.keys.toList();
  }

  /// Returns total disk usage of all offline files in bytes.
  Future<int> getTotalCacheSize() async {
    final dir = await _offlineDir();
    if (!await dir.exists()) return 0;

    int total = 0;
    await for (final entity in dir.list(recursive: true)) {
      if (entity is File) {
        total += await entity.length();
      }
    }
    return total;
  }

  /// Sync initial download states from manifest on startup.
  Future<void> initialize() async {
    final manifest = await _readManifest();
    for (final id in manifest.keys) {
      _states[id] =
          const DownloadState(status: DownloadStatus.done, progress: 1);
    }
    _downloadStates.add(Map.from(_states));
  }

  void _updateState(String contentItemId, DownloadState state) {
    _states[contentItemId] = state;
    _downloadStates.add(Map.from(_states));
  }

  void dispose() {
    _downloadStates.close();
  }
}
