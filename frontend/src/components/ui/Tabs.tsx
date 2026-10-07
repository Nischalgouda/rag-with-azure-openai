import { useId, useRef, useState, type KeyboardEvent, type ReactNode } from "react";

import styles from "./Tabs.module.css";

export interface TabItem {
  id: string;
  label: string;
  count?: number;
  panel: ReactNode;
}

interface Props {
  label: string;
  tabs: readonly TabItem[];
  defaultId?: string;
}

/**
 * WAI-ARIA tabs pattern: roving tabindex (only the active tab is in the Tab order),
 * ArrowLeft/ArrowRight/Home/End move and activate, panels are labelled by their tab.
 */
export function Tabs({ label, tabs, defaultId }: Props) {
  const uid = useId();
  const [activeId, setActiveId] = useState(defaultId ?? tabs[0]?.id ?? "");
  const refs = useRef<Record<string, HTMLButtonElement | null>>({});

  function move(index: number) {
    const next = tabs[(index + tabs.length) % tabs.length];
    if (!next) return;
    setActiveId(next.id);
    refs.current[next.id]?.focus();
  }

  function onKeyDown(event: KeyboardEvent, index: number) {
    switch (event.key) {
      case "ArrowRight":
        event.preventDefault();
        move(index + 1);
        break;
      case "ArrowLeft":
        event.preventDefault();
        move(index - 1);
        break;
      case "Home":
        event.preventDefault();
        move(0);
        break;
      case "End":
        event.preventDefault();
        move(tabs.length - 1);
        break;
    }
  }

  const active = tabs.find((t) => t.id === activeId) ?? tabs[0];

  return (
    <div>
      <div role="tablist" aria-label={label} className={styles.list}>
        {tabs.map((tab, index) => {
          const selected = tab.id === active?.id;
          return (
            <button
              key={tab.id}
              ref={(el) => {
                refs.current[tab.id] = el;
              }}
              role="tab"
              type="button"
              id={`${uid}-tab-${tab.id}`}
              aria-selected={selected}
              aria-controls={`${uid}-panel-${tab.id}`}
              tabIndex={selected ? 0 : -1}
              className={styles.tab}
              onClick={() => setActiveId(tab.id)}
              onKeyDown={(e) => onKeyDown(e, index)}
            >
              {tab.label}
              {tab.count !== undefined && <span className={styles.count}>{tab.count}</span>}
            </button>
          );
        })}
      </div>
      {active && (
        <div
          role="tabpanel"
          id={`${uid}-panel-${active.id}`}
          aria-labelledby={`${uid}-tab-${active.id}`}
          className={styles.panel}
        >
          {active.panel}
        </div>
      )}
    </div>
  );
}
