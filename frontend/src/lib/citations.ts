export type Segment = { type: "text"; value: string } | { type: "cite"; source: string };

const CITATION = /\[([^\]\n]+\.(?:md|txt|pdf))\]/gi;

/**
 * Split an answer into plain text and `[file.md]` citation segments.
 * The answer is rendered as React text nodes (never as HTML), so model output cannot inject markup.
 */
export function splitCitations(text: string): Segment[] {
  const segments: Segment[] = [];
  let last = 0;
  for (const match of text.matchAll(CITATION)) {
    const index = match.index ?? 0;
    if (index > last) segments.push({ type: "text", value: text.slice(last, index) });
    const source = match[1];
    if (source) segments.push({ type: "cite", source });
    last = index + match[0].length;
  }
  if (last < text.length) segments.push({ type: "text", value: text.slice(last) });
  return segments;
}
