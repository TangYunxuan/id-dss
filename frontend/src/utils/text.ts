/**
 * Text utilities shared across views.
 */

/**
 * Best-effort cleanup for common markdown artifacts in model outputs.
 * Keeps plain text, removes common markdown formatting so UI/export is readable.
 */
export function stripMarkdown(text: string): string {
  return (
    (text || '')
      // code fences
      .replace(/```[\s\S]*?```/g, (block) =>
        block.replace(/```[a-zA-Z]*\n?/g, '').replace(/```/g, '')
      )
      // links: [text](url) -> text
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '$1')
      // inline code
      .replace(/`([^`]+)`/g, '$1')
      // headings
      .replace(/^\s{0,3}#{1,6}\s+/gm, '')
      // blockquotes
      .replace(/^\s{0,3}>\s?/gm, '')
      // list markers (-, *, •, 1.)
      .replace(/^\s*(?:[-*•]|\d+\.)\s+/gm, '')
      // emphasis markers
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/__([^_]+)__/g, '$1')
      .replace(/\*([^*]+)\*/g, '$1')
      .replace(/_([^_]+)_/g, '$1')
      // collapse trailing whitespace per-line
      .replace(/[ \t]+$/gm, '')
      .trim()
  )
}

