export const formatScore = (value: number): string => value.toFixed(2);

export function formatLatency(ms: number): string {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)} s` : `${Math.round(ms)} ms`;
}

export const formatInt = (value: number): string => new Intl.NumberFormat("en").format(value);

export const plural = (n: number, one: string, many = `${one}s`): string =>
  `${n} ${n === 1 ? one : many}`;
