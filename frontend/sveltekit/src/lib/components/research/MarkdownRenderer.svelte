<script lang="ts">
  import { marked } from 'marked';
  import { onMount } from 'svelte';

  interface Props {
    content: string;
  }

  let { content }: Props = $props();

  let html = $state('');

  $effect(() => {
    const result = marked(content, { breaks: true, gfm: true });
    html = typeof result === 'string' ? result : '';
  });
</script>

<div class="meridian-prose">
  {@html html}
</div>

<style>
  .meridian-prose {
    color: var(--text-secondary);
    font-size: 14px;
    line-height: 1.7;
  }

  .meridian-prose :global(h1) {
    font-size: 20px;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: -0.01em;
    margin: 0 0 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-default);
  }

  .meridian-prose :global(h2) {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 24px 0 10px;
  }

  .meridian-prose :global(h3) {
    font-size: 14px;
    font-weight: 500;
    color: var(--text-primary);
    margin: 20px 0 8px;
  }

  .meridian-prose :global(p) {
    margin: 0 0 14px;
    color: var(--text-secondary);
  }

  .meridian-prose :global(ul),
  .meridian-prose :global(ol) {
    padding-left: 20px;
    margin: 0 0 14px;
  }

  .meridian-prose :global(li) {
    margin-bottom: 6px;
    color: var(--text-secondary);
  }

  .meridian-prose :global(strong) {
    font-weight: 600;
    color: var(--text-primary);
  }

  .meridian-prose :global(em) {
    color: var(--text-muted);
    font-style: italic;
  }

  .meridian-prose :global(blockquote) {
    border-left: 3px solid var(--border-hover);
    padding: 8px 16px;
    margin: 16px 0;
    color: var(--text-muted);
    background: var(--bg-elevated);
    border-radius: 0 6px 6px 0;
  }

  .meridian-prose :global(code) {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    background: var(--bg-elevated);
    border: 1px solid var(--border-default);
    padding: 1px 6px;
    border-radius: 4px;
    color: var(--text-primary);
  }

  .meridian-prose :global(pre) {
    background: var(--bg-elevated);
    border: 1px solid var(--border-default);
    border-radius: 8px;
    padding: 16px;
    overflow-x: auto;
    margin: 16px 0;
  }

  .meridian-prose :global(pre code) {
    background: none;
    border: none;
    padding: 0;
  }

  .meridian-prose :global(hr) {
    border: none;
    border-top: 1px solid var(--border-default);
    margin: 24px 0;
  }
</style>
