<script lang="ts">
	import type { Block, Notable } from '$lib/types/analysis';
	import MiniChart from '$lib/components/MiniChart.svelte';
	import { resolveChartColors } from '$lib/utils/chart-colors';

	let { block, notable }: { block: Block; notable?: Notable } = $props();

	let chartColors = $state(resolveChartColors());

	$effect(() => {
		chartColors = resolveChartColors();
	});

	// Sentence lengths bar chart data
	let sentenceLengthsData = $derived({
		labels: block.sentence_lengths.map((_, i) => i + 1),
		datasets: [{
			label: 'Sentence length',
			data: block.sentence_lengths,
			backgroundColor: chartColors.blueFill,
			borderColor: chartColors.blue,
			borderWidth: 1
		}]
	});

	// Notable badges: check which notable lists contain this block
	let notableBadges = $derived(() => {
		if (!notable) return [];
		const badges: string[] = [];
		if (notable.longest_sentences.includes(block.id)) badges.push('Longest sentences');
		if (notable.highest_mattr.includes(block.id)) badges.push('Highest MATTR');
		if (notable.highest_fog.includes(block.id)) badges.push('Highest Fog');
		if (notable.shortest_sentences.includes(block.id)) badges.push('Shortest sentences');
		return badges;
	});

	const metrics: { label: string; value: string }[] = $derived([
		{ label: 'MATTR', value: block.metrics.mattr.toFixed(3) },
		{ label: 'Flesch', value: block.metrics.flesch_ease.toFixed(1) },
		{ label: 'Fog', value: block.metrics.gunning_fog.toFixed(1) },
		...(block.metrics.coleman_liau != null ? [{ label: 'Coleman-Liau', value: block.metrics.coleman_liau.toFixed(1) }] : []),
		...(block.metrics.smog != null ? [{ label: 'SMOG', value: block.metrics.smog.toFixed(1) }] : []),
		...(block.metrics.ari != null ? [{ label: 'ARI', value: block.metrics.ari.toFixed(1) }] : []),
		{ label: 'Avg sent len', value: block.metrics.avg_sentence_length.toFixed(1) },
		{ label: 'Max sent len', value: String(block.metrics.max_sentence_length) },
	]);
</script>

<div class="metrics-panel card">
	<h4>Metrics</h4>

	<div class="metrics-grid">
		{#each metrics as m}
			<div class="metric-item">
				<span class="metric-label">{m.label}</span>
				<span class="metric-value mono">{m.value}</span>
			</div>
		{/each}
	</div>

	{#if notableBadges().length > 0}
		<div class="notable-badges">
			{#each notableBadges() as badge}
				<span class="notable-badge">{badge}</span>
			{/each}
		</div>
	{/if}

	{#if block.sentence_lengths.length > 0}
		<div class="sentence-chart">
			<span class="section-label">Sentence lengths</span>
			<MiniChart data={sentenceLengthsData} type="bar" label="Sentence lengths in block {block.id}" />
		</div>
	{/if}
</div>

<style>
	.metrics-panel {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.metrics-panel h4 {
		font-size: 0.85rem;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	.metrics-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.4rem 1rem;
	}

	.metric-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.metric-label {
		font-size: 0.8rem;
		color: var(--text-secondary);
	}

	.metric-value {
		font-size: 0.85rem;
	}

	.notable-badges {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
	}

	.notable-badge {
		display: inline-block;
		padding: 0.15rem 0.5rem;
		background: var(--chart-rose-fill);
		color: var(--chart-rose);
		border-radius: 3px;
		font-size: 0.75rem;
		font-family: var(--font-mono);
	}

	.sentence-chart {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.section-label {
		font-size: 0.75rem;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}
</style>
