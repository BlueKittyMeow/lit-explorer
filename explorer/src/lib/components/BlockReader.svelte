<script lang="ts">
	import type { Block } from '$lib/types/analysis';

	let { block, chapterTitle }: { block: Block; chapterTitle?: string } = $props();
</script>

<div class="block-reader card">
	<div class="block-header">
		<span class="block-id mono">Block {block.id}</span>
		{#if chapterTitle}
			<span class="chip">{chapterTitle}</span>
		{/if}
		<span class="block-stats mono">{block.word_count} words · {block.sentence_count} sentences</span>
	</div>

	<p class="preview-text">{block.preview}</p>

	{#if block.longest_sentence_preview && block.longest_sentence_preview !== block.preview}
		<div class="longest-sentence">
			<span class="section-label">Longest sentence</span>
			<p class="preview-text">{block.longest_sentence_preview}</p>
		</div>
	{/if}
</div>

<style>
	.block-reader {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.block-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.block-id {
		font-size: 0.9rem;
		font-weight: 500;
		color: var(--accent);
	}

	.block-stats {
		font-size: 0.8rem;
		color: var(--text-muted);
	}

	.preview-text {
		font-family: var(--font-serif);
		font-size: 0.95rem;
		line-height: 1.7;
		color: var(--text-primary);
	}

	.longest-sentence {
		border-top: 1px solid var(--border);
		padding-top: 0.5rem;
	}

	.section-label {
		font-size: 0.75rem;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.04em;
		display: block;
		margin-bottom: 0.25rem;
	}
</style>
