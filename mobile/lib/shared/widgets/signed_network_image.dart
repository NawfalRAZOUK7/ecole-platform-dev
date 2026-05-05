import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';

class SignedNetworkImage extends ConsumerStatefulWidget {
  final String path;
  final double? width;
  final double? height;
  final BoxFit? fit;
  final AlignmentGeometry alignment;
  final ImageErrorWidgetBuilder? errorBuilder;
  final ImageLoadingBuilder? loadingBuilder;

  const SignedNetworkImage({
    super.key,
    required this.path,
    this.width,
    this.height,
    this.fit,
    this.alignment = Alignment.center,
    this.errorBuilder,
    this.loadingBuilder,
  });

  @override
  ConsumerState<SignedNetworkImage> createState() => _SignedNetworkImageState();
}

class _SignedNetworkImageState extends ConsumerState<SignedNetworkImage> {
  late Future<String> _urlFuture;
  bool _retriedImageError = false;

  @override
  void initState() {
    super.initState();
    _urlFuture = _loadUrl();
  }

  @override
  void didUpdateWidget(SignedNetworkImage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.path != widget.path) {
      _retriedImageError = false;
      _urlFuture = _loadUrl();
    }
  }

  Future<String> _loadUrl({bool forceRefresh = false}) {
    return ref
        .read(signedUrlCacheProvider)
        .getUrl(widget.path, forceRefresh: forceRefresh);
  }

  @override
  Widget build(BuildContext context) {
    if (widget.path.trim().isEmpty) {
      return _buildError(context, ArgumentError('Missing image path'), null);
    }

    return FutureBuilder<String>(
      future: _urlFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return _buildLoading();
        }
        if (snapshot.hasError || snapshot.data == null) {
          return _buildError(context, snapshot.error, snapshot.stackTrace);
        }

        return Image.network(
          snapshot.data!,
          width: widget.width,
          height: widget.height,
          fit: widget.fit,
          alignment: widget.alignment,
          errorBuilder: _handleImageError,
          loadingBuilder: widget.loadingBuilder,
        );
      },
    );
  }

  Widget _handleImageError(
    BuildContext context,
    Object error,
    StackTrace? stackTrace,
  ) {
    if (!_retriedImageError) {
      _retriedImageError = true;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        ref.read(signedUrlCacheProvider).invalidate(widget.path);
        setState(() {
          _urlFuture = _loadUrl(forceRefresh: true);
        });
      });
      return _buildLoading();
    }
    return _buildError(context, error, stackTrace);
  }

  Widget _buildLoading() {
    return SizedBox(
      width: widget.width,
      height: widget.height,
      child: const Center(child: CircularProgressIndicator()),
    );
  }

  Widget _buildError(
    BuildContext context,
    Object? error,
    StackTrace? stackTrace,
  ) {
    final builder = widget.errorBuilder;
    if (builder != null) {
      return builder(
        context,
        error ?? StateError('Image unavailable'),
        stackTrace,
      );
    }
    return SizedBox(
      width: widget.width,
      height: widget.height,
      child: const Center(child: Icon(Icons.broken_image_outlined)),
    );
  }
}
