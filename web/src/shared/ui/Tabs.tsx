import { useEffect, useId, useMemo, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

interface TabItem {
  id: string;
  label: string;
  content: ReactNode;
}

interface TabsProps {
  tabs: TabItem[];
  defaultTab?: string;
  onChange?: (tabId: string) => void;
}

export function Tabs({ tabs, defaultTab, onChange }: TabsProps) {
  const { t } = useTranslation();
  const tabsId = useId();
  const initialTab = useMemo(() => defaultTab || tabs[0]?.id || '', [defaultTab, tabs]);
  const [activeTab, setActiveTab] = useState(initialTab);

  useEffect(() => {
    if (!tabs.some((tab) => tab.id === activeTab)) {
      setActiveTab(initialTab);
    }
  }, [activeTab, initialTab, tabs]);

  const activeIndex = tabs.findIndex((tab) => tab.id === activeTab);

  function activate(tabId: string) {
    setActiveTab(tabId);
    onChange?.(tabId);
  }

  return (
    <div className="tabs">
      <div className="tabs__list" role="tablist" aria-label={t('tabs.list', { defaultValue: 'Tabs' })}>
        {tabs.map((tab, index) => {
          const panelId = `${tabsId}-panel-${tab.id}`;
          const tabId = `${tabsId}-tab-${tab.id}`;
          const isSelected = tab.id === activeTab;

          return (
            <button
              key={tab.id}
              id={tabId}
              type="button"
              className={`tabs__tab ${isSelected ? 'tabs__tab--active' : ''}`}
              role="tab"
              aria-selected={isSelected}
              aria-controls={panelId}
              tabIndex={isSelected ? 0 : -1}
              onClick={() => activate(tab.id)}
              onKeyDown={(event) => {
                if (event.key === 'ArrowRight') {
                  const next = tabs[(index + 1) % tabs.length];
                  activate(next.id);
                }
                if (event.key === 'ArrowLeft') {
                  const previous = tabs[(index - 1 + tabs.length) % tabs.length];
                  activate(previous.id);
                }
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault();
                  activate(tab.id);
                }
              }}
            >
              {t(tab.label)}
            </button>
          );
        })}
      </div>

      {tabs.map((tab, index) => {
        const isSelected = index === activeIndex;
        const panelId = `${tabsId}-panel-${tab.id}`;
        const tabId = `${tabsId}-tab-${tab.id}`;

        return (
          <div
            key={tab.id}
            id={panelId}
            className="tabs__panel"
            role="tabpanel"
            aria-labelledby={tabId}
            hidden={!isSelected}
          >
            {isSelected ? tab.content : null}
          </div>
        );
      })}
    </div>
  );
}
