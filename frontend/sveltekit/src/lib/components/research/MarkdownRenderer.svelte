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

<div class="nova-prose">
  {@html html}
</div>

<style>
  .nova-prose {
    color: var(--text-secondary);
    font-size: 14px;
    line-height: 1.7;
  }

  .nova-prose :global(h1) {
    font-size: 20px;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: -0.01em;
    margin: 0 0 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-default);
  }

  .nova-prose :global(h2) {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 24px 0 10px;
  }

  .nova-prose :global(h3) {
    font-size: 14px;
    font-weight: 500;
    color: var(--text-primary);
    margin: 20px 0 8px;
  }

  .nova-prose :global(p) {
    margin: 0 0 14px;
    color: var(--text-secondary);
  }

  .nova-prose :global(ul),
  .nova-prose :global(ol) {
    padding-left: 20px;
    margin: 0 0 14px;
  }

  .nova-prose :global(li) {
    margin-bottom: 6px;
    color: var(--text-secondary);
  }

  .nova-prose :global(strong) {
    font-weight: 600;
    color: var(--text-primary);
  }

  .nova-prose :global(em) {
    color: var(--text-muted);
    font-style: italic;
  }

  .nova-prose :global(blockquote) {
    border-left: 3px solid var(--border-hover);
    padding: 8px 16px;
    margin: 16px 0;
    color: var(--text-muted);
    background: var(--bg-elevated);
    border-radius: 0 6px 6px 0;
  }

  .nova-prose :global(code) {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    background: var(--bg-elevated);
    border: 1px solid var(--border-default);
    padding: 1px 6px;
    border-radius: 4px;
    color: var(--text-primary);
  }

  .nova-prose :global(pre) {
    background: var(--bg-elevated);
    border: 1px solid var(--border-default);
    border-radius: 8px;
    padding: 16px;
    overflow-x: auto;
    margin: 16px 0;
  }

  .nova-prose :global(pre code) {
    background: none;
    border: none;
    padding: 0;
  }

  .nova-prose :global(hr) {
    border: none;
    border-top: 1px solid var(--border-default);
    margin: 24px 0;
  }
</style>
