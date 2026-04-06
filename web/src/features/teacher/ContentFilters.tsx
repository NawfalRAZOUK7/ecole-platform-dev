import { useTranslation } from 'react-i18next';
import { LEVEL_OPTIONS, SUBJECT_OPTIONS, type ContentFiltersProps } from './content-library.types';

export function ContentFilters({
  filterLevel,
  filterOrigin,
  filterSubject,
  filterType,
  onChangeLevel,
  onChangeOrigin,
  onChangeSubject,
  onChangeType,
}: ContentFiltersProps) {
  const { t } = useTranslation();

  return (
    <div className="filters-bar" style={{ marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
      <select className="filter-select" value={filterType} onChange={(event) => onChangeType(event.target.value)}>
        <option value="">{t('teacherContent.allTypes')}</option>
        <option value="video">{t('cms.contentTypes.video')}</option>
        <option value="pdf">{t('cms.contentTypes.pdf')}</option>
        <option value="audio">{t('cms.contentTypes.audio')}</option>
        <option value="interactive">{t('cms.contentTypes.interactive')}</option>
      </select>
      <select className="filter-select" value={filterSubject} onChange={(event) => onChangeSubject(event.target.value)}>
        <option value="">{t('teacherContent.allSubjects')}</option>
        {SUBJECT_OPTIONS.map((subject) => (
          <option key={subject} value={subject}>{t(`cms.subjects.${subject}`, subject)}</option>
        ))}
      </select>
      <select className="filter-select" value={filterLevel} onChange={(event) => onChangeLevel(event.target.value)}>
        <option value="">{t('teacherContent.allLevels')}</option>
        {LEVEL_OPTIONS.map((level) => (
          <option key={level} value={level}>{level}</option>
        ))}
      </select>
      <select className="filter-select" value={filterOrigin} onChange={(event) => onChangeOrigin(event.target.value)}>
        <option value="">{t('teacherContent.allOrigins')}</option>
        <option value="PLATFORM">{t('cms.origins.PLATFORM')}</option>
        <option value="PROMOTED">{t('cms.origins.PROMOTED')}</option>
      </select>
    </div>
  );
}
