import type { ReactNode } from "react";
import "./FilterTray.css";

interface FilterTrayProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
}

export function FilterTray({ open, onClose, children }: FilterTrayProps) {
  return (
    <>
      <div
        className={`filter-tray__backdrop${open ? " filter-tray__backdrop--open" : ""}`}
        onClick={onClose}
        aria-hidden="true"
      />
      <aside className={`filter-tray${open ? " filter-tray--open" : ""}`} aria-hidden={!open}>
        <div className="filter-tray__header">
          <h2>Filters</h2>
          <button type="button" className="filter-tray__close" onClick={onClose} aria-label="Close filters">
            ✕
          </button>
        </div>
        <div className="filter-tray__body">{children}</div>
      </aside>
    </>
  );
}

interface FilterSectionProps {
  title: string;
  children: ReactNode;
}

export function FilterSection({ title, children }: FilterSectionProps) {
  return (
    <div className="filter-tray__section">
      <h3>{title}</h3>
      {children}
    </div>
  );
}
