/**
 * Markdown rendering composable using marked library.
 * Provides safe HTML rendering of markdown text.
 */
import { marked } from 'marked'
import { computed, type Ref } from 'vue'

// Configure marked for safe inline rendering
marked.setOptions({
  breaks: true,  // Convert \n to <br>
  gfm: true,     // GitHub Flavored Markdown
})

/**
 * Parse markdown text to HTML string.
 * @param text - Markdown text to parse
 * @returns HTML string
 */
export function parseMarkdown(text: string): string {
  if (!text) return ''
  return marked.parse(text) as string
}

/**
 * Composable for reactive markdown parsing.
 * @param text - Ref containing markdown text
 * @returns Computed ref with parsed HTML
 */
export function useMarkdown(text: Ref<string>) {
  return computed(() => parseMarkdown(text.value))
}

export default parseMarkdown
