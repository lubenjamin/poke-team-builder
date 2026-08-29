import { TYPE_COLORS, typeColor } from "./typeColors";
import "./TypeFilter.css";

interface TypeFilterProps {
  selected: Set<string>;
  onToggle: (type: string) => void;
  onClear: () => void;
}

export function TypeFilter({ selected, onToggle, onClear }: TypeFilterProps) {
  return (
    <div className="type-filter">
      {Object.keys(TYPE_COLORS).map((type) => {
        const isActive = selected.has(type);
        return (
          <button
            key={type}
            type="button"
            className={`type-filter__chip${isActive ? " type-filter__chip--active" : ""}`}
            style={{ backgroundColor: typeColor(type) }}
            onClick={() => onToggle(type)}
            aria-pressed={isActive}
          >
            {type}
          </button>
        );
      })}
      {selected.size > 0 && (
        <button type="button" className="type-filter__clear" onClick={onClear}>
          Clear
        </button>
      )}
    </div>
  );
}
