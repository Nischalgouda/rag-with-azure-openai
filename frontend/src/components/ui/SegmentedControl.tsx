import styles from "./SegmentedControl.module.css";

export interface SegmentedOption<T extends string> {
  value: T;
  label: string;
}

interface Props<T extends string> {
  /** Accessible group name, announced by screen readers. */
  legend: string;
  /** Radios in one group must share a name. */
  name: string;
  value: T;
  options: readonly SegmentedOption<T>[];
  onChange: (value: T) => void;
  disabled?: boolean;
  /** Show the legend as a visible label (default: visually hidden). */
  showLegend?: boolean;
}

/**
 * A segmented control built on native radio inputs, so keyboard behaviour (arrow keys, focus,
 * single selection) and screen-reader semantics come from the platform, not from custom ARIA.
 */
export function SegmentedControl<T extends string>({
  legend,
  name,
  value,
  options,
  onChange,
  disabled = false,
  showLegend = false,
}: Props<T>) {
  return (
    <fieldset className={styles.group} disabled={disabled}>
      <legend className={showLegend ? styles.legend : "sr-only"}>{legend}</legend>
      <div className={styles.track}>
        {options.map((option) => (
          <label key={option.value} className={styles.option}>
            <input
              className={styles.input}
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
            />
            <span className={styles.label}>{option.label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
