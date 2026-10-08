interface Props {
  size?: number;
  className?: string;
}

/**
 * The RAG X-ray mark: three chunks scored against the refusal threshold. The first bar clears the line (blue),
 * the other two fall short of it (orange). It is the product's whole idea in one glyph, and the same bars-and-rule
 * motif appears in the chart. Decorative: the wordmark beside it carries the name.
 */
export function Logo({ size = 28, className }: Props) {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      width={size}
      height={size}
      viewBox="0 0 32 32"
      className={className}
    >
      <rect width="32" height="32" rx="8" fill="var(--ink)" />
      <rect x="7" y="8" width="17" height="4" rx="2" fill="#3987e5" />
      <rect x="7" y="14" width="11" height="4" rx="2" fill="#d95926" />
      <rect x="7" y="20" width="6" height="4" rx="2" fill="#d95926" />
      <rect x="19" y="5" width="2" height="22" rx="1" fill="var(--on-ink)" />
    </svg>
  );
}
