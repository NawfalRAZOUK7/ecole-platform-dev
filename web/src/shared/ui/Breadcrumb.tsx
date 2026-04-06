import { memo } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

export const Breadcrumb = memo(function Breadcrumb({ items }: BreadcrumbProps) {
  const { t, i18n } = useTranslation();
  const separator = i18n.dir() === 'rtl' ? '←' : '/';

  return (
    <nav className="breadcrumb" aria-label={t('breadcrumb.label', { defaultValue: 'breadcrumb' })}>
      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        return (
          <span key={`${item.label}-${index}`} className="breadcrumb__item">
            {item.href && !isLast ? (
              <Link to={item.href}>{t(item.label)}</Link>
            ) : (
              <span aria-current={isLast ? 'page' : undefined}>{t(item.label)}</span>
            )}
            {!isLast && (
              <span className="breadcrumb__separator" aria-hidden="true">
                {separator}
              </span>
            )}
          </span>
        );
      })}
    </nav>
  );
});
