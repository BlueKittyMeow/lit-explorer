<script lang="ts">
	import MetricCard from '$lib/components/MetricCard.svelte';
	import MiniChart from '$lib/components/MiniChart.svelte';

	let { data } = $props();

	let avgFlesch = $derived(data.analysis.blocks.length
		? (data.analysis.blocks.reduce((s, b) => s + b.metrics.flesch_ease, 0) / data.analysis.blocks.length).toFixed(1)
		: '—');

	let avgFog = $derived(data.analysis.blocks.length
		? (data.analysis.blocks.reduce((s, b) => s + b.metrics.gunning_fog, 0) / data.analysis.blocks.length).toFixed(1)
		: '—');

	let sentimentChartData = $derived({
		labels: data.sentiment.arc.map((p) => p.position),
		datasets: [
			{
				label: 'Sentiment',
				data: data.sentiment.arc.map((p) => p.compound),
				borderColor: 'hsl(220, 50%, 55%)',
				backgroundColor: 'hsla(220, 50%, 55%, 0.1)',
				fill: true,
				tension: 0.3,
				pointRadius: 0
			}
		]
	});

	let mattrChartData = $derived({
		labels: data.analysis.blocks.map((b) => b.id),
		datasets: [
			{
				label: 'MATTR',
				data: data.analysis.blocks.map((b) => b.metrics.mattr),
				borderColor: 'hsl(150, 45%, 45%)',
				backgroundColor: 'hsla(150, 45%, 45%, 0.1)',
				fill: true,
				tension: 0.3,
				pointRadius: 0
			}
		]
	});
</script>

<section class="overview">
	<div class="metrics-row">
		<MetricCard label="Words" value={data.manifest.word_count.toLocaleString()} />
		<MetricCard label="Blocks" value={data.analysis.total_blocks} />
		<MetricCard label="Chapters" value={data.manifest.chapter_count} />
		<MetricCard label="Characters" value={data.manifest.character_list.length} />
		<MetricCard label="Avg Flesch" value={avgFlesch} subtitle="ease score" />
		<MetricCard label="Avg Fog" value={avgFog} subtitle="grade level" />
	</div>

	<div class="charts-row">
		<div class="chart-container card">
			<h3>Sentiment Arc</h3>
			<MiniChart data={sentimentChartData} label="Sentiment arc across the text" />
		</div>
		<div class="chart-container card">
			<h3>Vocabulary Richness (MATTR)</h3>
			<MiniChart data={mattrChartData} label="MATTR per block across the text" />
		</div>
	</div>

	{#if data.analysis.pacing}
		<div class="pacing-section card">
			<h3>Pacing</h3>
			<div class="pacing-stats mono">
				<span>{data.analysis.pacing.sentence_count} sentences</span>
				<span class="sep">·</span>
				<span>mean length {data.analysis.pacing.distribution.mean.toFixed(1)}</span>
				<span class="sep">·</span>
				<span>std dev {data.analysis.pacing.distribution.std_dev.toFixed(1)}</span>
			</div>
			{#if data.analysis.pacing.flowing_passages.length > 0}
				<div class="passage-list">
					<h4>Flowing passages</h4>
					{#each data.analysis.pacing.flowing_passages as passage}
						<p class="passage-preview">
							Block {passage.block_id}: avg {passage.avg_sentence_length.toFixed(1)} words/sentence
							— <em>"{passage.preview}"</em>
						</p>
					{/each}
				</div>
			{/if}
			{#if data.analysis.pacing.staccato_passages.length > 0}
				<div class="passage-list">
					<h4>Staccato passages</h4>
					{#each data.analysis.pacing.staccato_passages as passage}
						<p class="passage-preview">
							Block {passage.block_id}: avg {passage.avg_sentence_length.toFixed(1)} words/sentence
							— <em>"{passage.preview}"</em>
						</p>
					{/each}
				</div>
			{/if}
		</div>
	{/if}

	{#if data.sentiment.extremes.most_positive || data.sentiment.extremes.most_negative}
		<div class="extremes card">
			<h3>Sentiment Extremes</h3>
			{#if data.sentiment.extremes.most_positive}
				<p>
					<strong>Most positive</strong> (score: {data.sentiment.extremes.most_positive.score.toFixed(3)}):
					<em>"{data.sentiment.extremes.most_positive.text_preview}"</em>
				</p>
			{/if}
			{#if data.sentiment.extremes.most_negative}
				<p>
					<strong>Most negative</strong> (score: {data.sentiment.extremes.most_negative.score.toFixed(3)}):
					<em>"{data.sentiment.extremes.most_negative.text_preview}"</em>
				</p>
			{/if}
		</div>
	{/if}
</section>

<style>
	.overview {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.metrics-row {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.charts-row {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 1rem;
	}

	.chart-container h3 {
		font-size: 0.95rem;
		margin-bottom: 0.5rem;
		color: var(--text-secondary);
	}

	.pacing-section h3,
	.extremes h3 {
		font-size: 0.95rem;
		margin-bottom: 0.5rem;
		color: var(--text-secondary);
	}

	.pacing-stats {
		font-size: 0.85rem;
		color: var(--text-secondary);
		margin-bottom: 0.75rem;
	}

	.sep {
		margin: 0 0.25rem;
		color: var(--text-muted);
	}

	.passage-list h4 {
		font-size: 0.85rem;
		margin: 0.5rem 0 0.25rem;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	.passage-preview {
		font-size: 0.85rem;
		color: var(--text-secondary);
		margin: 0.25rem 0;
	}

	.extremes p {
		font-size: 0.9rem;
		margin: 0.5rem 0;
	}
</style>
