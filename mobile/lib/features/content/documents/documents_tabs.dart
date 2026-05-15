part of 'documents_screen.dart';

extension _DocumentsTabs on _DocumentsScreenState {
  List<ManagedDocument> _filteredDocuments(List<ManagedDocument> items) {
    if (_selectedCategory.isEmpty) return items;
    return items.where((item) => item.category == _selectedCategory).toList();
  }

  Widget _buildDocumentsTab({
    required String title,
    required List<ManagedDocument> items,
    required bool studentLinked,
  }) {
    final t = AppLocalizations.of(ref);

    return RefreshIndicator(
      onRefresh: _bootstrap,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_error != null) ...[
            _ErrorCard(message: _error!),
            const SizedBox(height: 12),
          ],
          if (_uploading) ...[
            _UploadProgressCard(
              title: _uploadLabel.isEmpty
                  ? t.t('documents.uploading')
                  : _uploadLabel,
              progress: _uploadProgress,
            ),
            const SizedBox(height: 12),
          ],
          _CategoryChipBar(
            categories: _options.categories,
            selected: _selectedCategory,
            onChanged: (value) {
              _applyState(() => _selectedCategory = value);
            },
          ),
          if (_canUploadDocuments) ...[
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                OutlinedButton.icon(
                  onPressed: () => _pickAndUploadDocument(
                    fromCamera: false,
                    studentLinked: studentLinked,
                  ),
                  icon: const Icon(Icons.attach_file_outlined),
                  label: Text(t.t('documents.pickFile')),
                ),
                OutlinedButton.icon(
                  onPressed: () => _pickAndUploadDocument(
                    fromCamera: true,
                    studentLinked: studentLinked,
                  ),
                  icon: const Icon(Icons.camera_alt_outlined),
                  label: Text(t.t('documents.scan')),
                ),
              ],
            ),
          ],
          const SizedBox(height: 16),
          Text(title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          if (items.isEmpty)
            Center(child: Text(t.t('documents.empty')))
          else
            ...items.map(
              (item) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: _DocumentCard(
                  item: item,
                  locale: ref.read(localeProvider),
                  onTap: () => _openDocumentPreview(item),
                  onShare: () => _shareDocument(item),
                  onDelete: item.canDelete
                      ? () => _deleteDocument(
                            item,
                            hardDelete: item.canHardDelete,
                          )
                      : null,
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildStudentTab() {
    final t = AppLocalizations.of(ref);
    return RefreshIndicator(
      onRefresh: () async {
        await _bootstrap();
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_error != null) ...[
            _ErrorCard(message: _error!),
            const SizedBox(height: 12),
          ],
          if (_options.students.isEmpty)
            Center(child: Text(t.t('documents.noStudents')))
          else ...[
            DropdownButtonFormField<String>(
              key: ValueKey(_selectedStudentId),
              initialValue: _selectedStudentId.isEmpty
                  ? _options.students.first.id
                  : _selectedStudentId,
              decoration: InputDecoration(
                labelText: t.t('documents.studentSelector'),
              ),
              items: _options.students
                  .map(
                    (item) => DropdownMenuItem<String>(
                      value: item.id,
                      child: Text(item.fullName),
                    ),
                  )
                  .toList(),
              onChanged: (value) {
                if (value == null || value == _selectedStudentId) return;
                _applyState(() => _selectedStudentId = value);
                _reloadStudentData();
              },
            ),
            const SizedBox(height: 12),
            _CategoryChipBar(
              categories: _options.categories,
              selected: _selectedCategory,
              onChanged: (value) {
                _applyState(() => _selectedCategory = value);
              },
            ),
            if (_canUploadDocuments) ...[
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  OutlinedButton.icon(
                    onPressed: _selectedStudentId.isEmpty
                        ? null
                        : () => _pickAndUploadDocument(
                              fromCamera: false,
                              studentLinked: true,
                            ),
                    icon: const Icon(Icons.attach_file_outlined),
                    label: Text(t.t('documents.pickFile')),
                  ),
                  OutlinedButton.icon(
                    onPressed: _selectedStudentId.isEmpty
                        ? null
                        : () => _pickAndUploadDocument(
                              fromCamera: true,
                              studentLinked: true,
                            ),
                    icon: const Icon(Icons.camera_alt_outlined),
                    label: Text(t.t('documents.scan')),
                  ),
                ],
              ),
            ],
            const SizedBox(height: 16),
            Text(
              t.t('documents.checklist'),
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            if (_checklist.isEmpty)
              Center(child: Text(t.t('documents.empty')))
            else
              ..._checklist.map(
                (item) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: _ChecklistCard(
                    item: item,
                    locale: ref.read(localeProvider),
                  ),
                ),
              ),
            const SizedBox(height: 16),
            Text(
              t.t('documents.studentDocuments'),
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            if (_studentDocuments.isEmpty)
              Center(child: Text(t.t('documents.empty')))
            else
              ..._filteredDocuments(_studentDocuments).map(
                (item) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: _DocumentCard(
                    item: item,
                    locale: ref.read(localeProvider),
                    onTap: () => _openDocumentPreview(item),
                    onShare: () => _shareDocument(item),
                    onDelete: item.canDelete
                        ? () => _deleteDocument(
                              item,
                              hardDelete: item.canHardDelete,
                            )
                        : null,
                  ),
                ),
              ),
          ],
        ],
      ),
    );
  }

  Widget _buildResourcesTab() {
    final t = AppLocalizations.of(ref);

    return RefreshIndicator(
      onRefresh: () async {
        await _reloadResources();
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_error != null) ...[
            _ErrorCard(message: _error!),
            const SizedBox(height: 12),
          ],
          if (_uploading) ...[
            _UploadProgressCard(
              title: _uploadLabel.isEmpty
                  ? t.t('documents.uploading')
                  : _uploadLabel,
              progress: _uploadProgress,
            ),
            const SizedBox(height: 12),
          ],
          TextField(
            controller: _resourceSearchController,
            decoration: InputDecoration(
              labelText: t.t('documents.search'),
              suffixIcon: IconButton(
                onPressed: () => _reloadResources(),
                icon: const Icon(Icons.search),
              ),
            ),
            textInputAction: TextInputAction.search,
            onSubmitted: (_) => _reloadResources(),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _resourceSubjectController,
                  decoration: InputDecoration(
                    labelText: t.t('documents.subject'),
                  ),
                  onSubmitted: (_) => _reloadResources(),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: _resourceLevelController,
                  decoration: InputDecoration(
                    labelText: t.t('documents.level'),
                  ),
                  onSubmitted: (_) => _reloadResources(),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              ChoiceChip(
                label: Text(t.t('documents.allTypes')),
                selected: _selectedResourceType.isEmpty,
                onSelected: (_) {
                  _applyState(() => _selectedResourceType = '');
                  _reloadResources();
                },
              ),
              ..._resourceTypes.map(
                (type) => ChoiceChip(
                  label: Text(t.t('documents.resourceTypes.$type')),
                  selected: _selectedResourceType == type,
                  onSelected: (_) {
                    _applyState(() => _selectedResourceType = type);
                    _reloadResources();
                  },
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<double?>(
            initialValue: _resourceMinRating,
            decoration: InputDecoration(
              labelText: t.t('documents.minRating'),
            ),
            items: [
              DropdownMenuItem<double?>(
                value: null,
                child: Text(t.t('documents.all')),
              ),
              const DropdownMenuItem<double?>(value: 4, child: Text('4+')),
              const DropdownMenuItem<double?>(value: 3, child: Text('3+')),
            ],
            onChanged: (value) {
              _applyState(() => _resourceMinRating = value);
              _reloadResources();
            },
          ),
          if (_canUploadResources) ...[
            const SizedBox(height: 12),
            Align(
              alignment: AlignmentDirectional.centerStart,
              child: OutlinedButton.icon(
                onPressed: _pickAndUploadResource,
                icon: const Icon(Icons.cloud_upload_outlined),
                label: Text(t.t('documents.uploadResource')),
              ),
            ),
          ],
          const SizedBox(height: 16),
          if (_resources.isEmpty)
            Center(child: Text(t.t('documents.resourcesEmpty')))
          else
            ..._resources.map(
              (resource) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: _ResourceCard(
                  item: resource,
                  locale: ref.read(localeProvider),
                  onTap: () => _openResource(resource),
                  onDownload: () => _shareResource(resource),
                  onRate:
                      resource.canRate ? () => _rateResource(resource) : null,
                  onDelete: resource.canDelete
                      ? () => _deleteResource(resource)
                      : null,
                ),
              ),
            ),
          if (_resourcesHasMore) ...[
            const SizedBox(height: 8),
            FilledButton.tonal(
              onPressed: _loadingMoreResources ? null : _loadMoreResources,
              child: _loadingMoreResources
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Text(t.t('documents.loadMore')),
            ),
          ],
        ],
      ),
    );
  }
}
