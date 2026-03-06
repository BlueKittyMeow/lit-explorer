<script lang="ts">
	import { page } from '$app/state';
	import MetricCard from '$lib/components/MetricCard.svelte';
	import type { Chapter } from '$lib/types/analysis';

	let { data } = $props();
	let slug = $derived(page.params.slug);

	// Summary stats
	let totalChapters = $derived(data.chapters.chapters.length);
	let avgWords = $derived(totalChapters
		? Math.round(data.chapters.chapters.reduce((s, c) => s + c.word_count, 0) / totalChapters).toLocaleString()
		: '—');
	let avgDialogue = $derived(totalChapters
		? (data.chapters.chapters.reduce((s, c) => s + c.dialogue_ratio, 0) / totalChapters * 100).toFixed(0) + '%'
		: '—');

	// Sort state
	type SortKey = keyof Pick<Chapter, 'number' | 'word_count' | 'sentence_count' | 'dialogue_ratio' | 'avg_sentence_length' | 'mattr' | 'flesch_ease' | 'fog'> | 'sentiment';
	let sortKey = $state<SortKey>('number');
	let sortAsc = $state(true);

	function toggleSort(key: SortKey) {
		if (sortKey === key) {
			sortAsc = !sortAsc;
		} else {
			sortKey = key;
			sortAsc = true;
		}
	}

	function getSortValue(chapter: Chapter, key: SortKey): number {
		if (key === 'sentiment') return chapter.sentiment.compound;
		return chapter[key] as number;
	}

	let sortedChapters = $derived(
		[...data.chapters.chapters].sort((a, b) => {
			const av = getSortValue(a, sortKey);
			const bv = getSortValue(b, sortKey);
			return sortAsc ? av - bv : bv - av;
		})
	);

	function ariaSort(key: SortKey): 'ascending' | 'descending' | 'none' {
		if (sortKey !== key) return 'none';
		return sortAsc ? 'ascending' : 'descending';
	}

	function sortIndicator(key: SortKey): string {
		if (sortKey !== key) return '';
		return sortAsc ? ' ▲' : ' ▼';
	}

	function sentimentClass(compound: number): string {
		if (compound > 0.1) return 'positive';
		if (compound < -0.1) return 'negative';
		return 'neutral';
	}

	const columns: { key: SortKey; label: string; hideOnMobile?: boolean }[] = [
		{ key: 'number', label: '#' },
		{ key: 'word_count', label: 'Words' },
		{ key: 'sentence_count', label: 'Sentences', hideOnMobile: true },
		{ key: 'dialogue_ratio', label: 'Dialogue' },
		{ key: 'avg_sentence_length', label: 'Avg Sent', hideOnMobile: true },
		{ key: 'mattr', label: 'MATTR', hideOnMobile: true },
		{ key: 'flesch_ease', label: 'Flesch', hideOnMobile: true },
		{ key: 'fog', label: 'Fog' },
		{ key: 'sentiment', label: 'Sent.' },
	];
</script>

<section class="chapters">
	<div class="metrics-row">
		<MetricCard label="Chapters" value={totalChapters} />
		<MetricCard label="Avg Words" value={avgWords} subtitle="per chapter" />
		<MetricCard label="Avg Dialogue" value={avgDialogue} subtitle="ratio" />
	</div>

	<div class="table-wrapper card">
		<table>
			<thead>
				<tr>
					{#each columns as col}
						<th
							aria-sort={ariaSort(col.key)}
							class:hide-mobile={col.hideOnMobile}
							class:sticky-col={col.key === 'number'}
						>
							<button onclick={() => toggleSort(col.key)}>
								{col.label}{sortIndicator(col.key)}
							</button>
						</th>
					{/each}
					<th>Title</th>
					<th>Character</th>
				</tr>
			</thead>
			<tbody>
				{#each sortedChapters as chapter (chapter.number)}
					<tr>
						<td class="mono sticky-col">
							<a href="/{slug}/blocks?from={chapter.block_range[0]}">{chapter.number}</a>
						</td>
						<td class="mono">{chapter.word_count.toLocaleString()}</td>
						<td class="mono hide-mobile">{chapter.sentence_count}</td>
						<td class="mono">{(chapter.dialogue_ratio * 100).toFixed(0)}%</td>
						<td class="mono hide-mobile">{chapter.avg_sentence_length.toFixed(1)}</td>
						<td class="mono hide-mobile">{chapter.mattr.toFixed(3)}</td>
						<td class="mono hide-mobile">{chapter.flesch_ease.toFixed(1)}</td>
						<td class="mono">{chapter.fog.toFixed(1)}</td>
						<td>
							<span class="sentiment-dot {sentimentClass(chapter.sentiment.compound)}"
								title="Sentiment: {chapter.sentiment.compound.toFixed(2)}"
							></span>
						</td>
						<td>{chapter.title}</td>
						<td><span class="chip">{chapter.dominant_character}</span></td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</section>

<style>
	.chapters {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.metrics-row {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.table-wrapper {
		overflow-x: auto;
		padding: 0.75rem;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.85rem;
	}

	th, td {
		padding: 0.5rem 0.75rem;
		text-align: left;
		white-space: nowrap;
	}

	th {
		border-bottom: 2px solid var(--border);
		color: var(--text-muted);
		font-weight: 500;
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	th button {
		background: none;
		border: none;
		color: inherit;
		font: inherit;
		cursor: pointer;
		padding: 0;
		text-transform: inherit;
		letter-spacing: inherit;
	}

	th button:hover {
		color: var(--accent);
	}

	td {
		border-bottom: 1px solid var(--border);
	}

	tr:last-child td {
		border-bottom: none;
	}

	td a {
		color: var(--accent);
		font-weight: 500;
	}

	.sentiment-dot {
		display: inline-block;
		width: 10px;
		height: 10px;
		border-radius: 50%;
	}

	.sentiment-dot.positive { background: var(--chart-green); }
	.sentiment-dot.neutral { background: var(--chart-amber); }
	.sentiment-dot.negative { background: var(--chart-rose); }

	.sticky-col {
		position: sticky;
		left: 0;
		background: var(--bg-card);
		z-index: 1;
	}

	@media (max-width: 768px) {
		.hide-mobile {
			display: none;
		}
	}
</style>
