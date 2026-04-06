import { useTranslation } from 'react-i18next';
import type { DocumentsTab } from './documents.service';
import type { DocumentViewMode } from './documents.types';
import { RESOURCE_TYPES } from './documents.types';

interface DocumentFiltersProps {
  activeTab: DocumentsTab;
  canUploadResources: boolean;
  documentCategoryFilter: string;
  documentFromDate: string;
  documentMimeOptions: string[];
  documentSearch: string;
  documentToDate: string;
  documentTypeFilter: string;
  optionsCategories: string[];
  resourceFilterLevel: string;
  resourceFilterRating: string;
  resourceFilterSubject: string;
  resourceFilterType: string;
  resourceFormOpen: boolean;
  resourceSearch: string;
  selectedDocumentCount: number;
  showHardDelete: boolean;
  viewMode: DocumentViewMode;
  onBulkDelete: () => void;
  onBulkDownload: () => void;
  onChangeActiveTab: (tab: DocumentsTab) => void;
  onChangeDocumentCategoryFilter: (value: string) => void;
  onChangeDocumentFromDate: (value: string) => void;
  onChangeDocumentSearch: (value: string) => void;
  onChangeDocumentToDate: (value: string) => void;
  onChangeDocumentTypeFilter: (value: string) => void;
  onChangeResourceFilterLevel: (value: string) => void;
  onChangeResourceFilterRating: (value: string) => void;
  onChangeResourceFilterSubject: (value: string) => void;
  onChangeResourceFilterType: (value: string) => void;
  onChangeResourceSearch: (value: string) => void;
  onHardDelete: () => void;
  onToggleResourceForm: () => void;
  onToggleViewMode: () => void;
}

export function DocumentFilters({
  activeTab,
  canUploadResources,
  documentCategoryFilter,
  documentFromDate,
  documentMimeOptions,
  documentSearch,
  documentToDate,
  documentTypeFilter,
  optionsCategories,
  resourceFilterLevel,
  resourceFilterRating,
  resourceFilterSubject,
  resourceFilterType,
  resourceFormOpen,
  resourceSearch,
  selectedDocumentCount,
  showHardDelete,
  viewMode,
  onBulkDelete,
  onBulkDownload,
  onChangeActiveTab,
  onChangeDocumentCategoryFilter,
  onChangeDocumentFromDate,
  onChangeDocumentSearch,
  onChangeDocumentToDate,
  onChangeDocumentTypeFilter,
  onChangeResourceFilterLevel,
  onChangeResourceFilterRating,
  onChangeResourceFilterSubject,
  onChangeResourceFilterType,
  onChangeResourceSearch,
  onHardDelete,
  onToggleResourceForm,
  onToggleViewMode,
}: DocumentFiltersProps) {
  const { t } = useTranslation();

  return (
    <>
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('documents.title')}</h1>
          <p className="page-subtitle">{t('documents.subtitle')}</p>
        </div>
        <div className="calendar-view-toggle">
          {(['mine', 'student', 'resources'] as DocumentsTab[]).map((tab) => (
            <button key={tab} type="button" className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-secondary'}`} onClick={() => onChangeActiveTab(tab)}>
              {t(`documents.tabs.${tab}`)}
            </button>
          ))}
        </div>
      </div>

      <div className="documents-toolbar">
        <div className="documents-toolbar__filters">
          {activeTab !== 'resources' ? (
            <>
              <input aria-label={t('documents.filters.search')} value={documentSearch} onChange={(event) => onChangeDocumentSearch(event.target.value)} placeholder={t('documents.filters.search')} />
              <select aria-label={t('documents.filters.allCategories')} value={documentCategoryFilter} onChange={(event) => onChangeDocumentCategoryFilter(event.target.value)}>
                <option value="">{t('documents.filters.allCategories')}</option>
                {optionsCategories.map((category) => <option key={category} value={category}>{t(`documents.categories.${category}`)}</option>)}
              </select>
              <select aria-label={t('documents.filters.allTypes')} value={documentTypeFilter} onChange={(event) => onChangeDocumentTypeFilter(event.target.value)}>
                <option value="">{t('documents.filters.allTypes')}</option>
                {documentMimeOptions.map((mime) => <option key={mime} value={mime}>{mime}</option>)}
              </select>
              <input aria-label={t('documents.filters.fromDate', { defaultValue: 'From date' })} type="date" value={documentFromDate} onChange={(event) => onChangeDocumentFromDate(event.target.value)} />
              <input aria-label={t('documents.filters.toDate', { defaultValue: 'To date' })} type="date" value={documentToDate} onChange={(event) => onChangeDocumentToDate(event.target.value)} />
            </>
          ) : (
            <>
              <input aria-label={t('documents.resources.searchPlaceholder')} value={resourceSearch} onChange={(event) => onChangeResourceSearch(event.target.value)} placeholder={t('documents.resources.searchPlaceholder')} />
              <input aria-label={t('documents.resources.subject')} value={resourceFilterSubject} onChange={(event) => onChangeResourceFilterSubject(event.target.value)} placeholder={t('documents.resources.subject')} />
              <input aria-label={t('documents.resources.level')} value={resourceFilterLevel} onChange={(event) => onChangeResourceFilterLevel(event.target.value)} placeholder={t('documents.resources.level')} />
              <select aria-label={t('documents.resources.allTypes')} value={resourceFilterType} onChange={(event) => onChangeResourceFilterType(event.target.value)}>
                <option value="">{t('documents.resources.allTypes')}</option>
                {RESOURCE_TYPES.map((item) => <option key={item} value={item}>{t(`documents.resourceTypes.${item}`)}</option>)}
              </select>
              <select aria-label={t('documents.resources.allRatings')} value={resourceFilterRating} onChange={(event) => onChangeResourceFilterRating(event.target.value)}>
                <option value="">{t('documents.resources.allRatings')}</option>
                {[5, 4, 3].map((rating) => <option key={rating} value={rating}>{t('documents.resources.ratingAtLeast', { rating })}</option>)}
              </select>
            </>
          )}
        </div>

        {activeTab !== 'resources' ? (
          <div className="documents-toolbar__actions">
            <button type="button" className="btn btn-secondary" onClick={onToggleViewMode}>
              {t(`documents.view.${viewMode === 'grid' ? 'list' : 'grid'}`)}
            </button>
            {selectedDocumentCount > 0 && (
              <>
                <button type="button" className="btn btn-secondary" onClick={onBulkDownload}>{t('documents.bulk.download')}</button>
                <button type="button" className="btn btn-secondary" onClick={onBulkDelete}>{t('documents.bulk.delete')}</button>
                {showHardDelete && <button type="button" className="btn btn-danger" onClick={onHardDelete}>{t('documents.bulk.hardDelete')}</button>}
              </>
            )}
          </div>
        ) : (
          canUploadResources && (
            <button type="button" className="btn btn-primary" onClick={onToggleResourceForm}>
              {resourceFormOpen ? t('app.close') : t('documents.resources.uploadAction')}
            </button>
          )
        )}
      </div>
    </>
  );
}
