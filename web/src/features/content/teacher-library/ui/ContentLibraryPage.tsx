/**
 * Teacher Content Library — browse platform + school content, assign to class,
 * upload school-scoped content, submit for platform review, view my submissions.
 *
 * Phase 10B — Teacher Content Library (Web)
 * API: GET /content/library, POST /content/assign, DELETE /content/assign/{id},
 *      POST /content/submit-for-review, GET /content/my-submissions
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ContentUploadPanel } from './ContentUploadPanel';
import { ContentSubmissionsTable } from './ContentSubmissionsTable';
import { LibraryGrid } from './LibraryGrid';
import type { ContentLibraryTab } from '../model/content-library.types';

export function ContentLibraryPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<ContentLibraryTab>('browse');

  return (
    <div className="page">
      <h1 className="page-title">{t('teacherContent.title')}</h1>
      <div className="filters-bar" style={{ marginBottom: 16 }}>
        {(['browse', 'upload', 'submissions'] as ContentLibraryTab[]).map((tabKey) => (
          <button
            key={tabKey}
            className={`btn ${tab === tabKey ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setTab(tabKey)}
            style={{ marginRight: 8 }}
          >
            {t(`teacherContent.tab_${tabKey}`)}
          </button>
        ))}
      </div>

      {tab === 'browse' && <LibraryGrid />}
      {tab === 'upload' && <ContentUploadPanel />}
      {tab === 'submissions' && <ContentSubmissionsTable />}
    </div>
  );
}
