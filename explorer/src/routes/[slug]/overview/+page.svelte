<script lang="ts">
	import { page } from '$app/state';
	import MetricCard from '$lib/components/MetricCard.svelte';
	import MiniChart from '$lib/components/MiniChart.svelte';

	let { data } = $props();
	let slug = $derived(page.params.slug);

	// Averages
	let avgFlesch = $derived(data.analysis.blocks.length
		? (data.analysis.blocks.reduce((s, b) => s + b.metrics.flesch_ease, 0) / data.analysis.blocks.length).toFixed(1)
		: '—');

	let avgFog = $derived(data.analysis.blocks.length
		? (data.analysis.blocks.reduce((s, b) => s + b.metrics.gunning_fog, 0) / data.analysis.blocks.length).toFixed(1)
		: '—');

	let avgDialogue = $derived(data.chapters.chapters.length
		? (data.chapters.chapters.reduce((s, c) => s + c.dialogue_ratio, 0) / data.chapters.chapters.length * 100).toFixed(0) + '%'
		: '—');

	// Resolve CSS variable chart colors for theme-awareness
	let chartColors = $state({ blue: '', blueFill: '', green: '', greenFill: '', amber: '', amberFill: '', rose: '', roseFill: '' });

	$effect(() => {
		const styles = getComputedStyle(document.documentElement);
		chartColors = {
			blue: styles.getPropertyValue('--chart-blue').trim(),
			blueFill: styles.getPropertyValue('--chart-blue-fill').trim(),
			green: styles.getPropertyValue('--chart-green').trim(),
			greenFill: styles.getPropertyValue('--chart-green-fill').trim(),
			amber: styles.getPropertyValue('--chart-amber').trim(),
			amberFill: styles.getPropertyValue('--chart-amber-fill').trim(),
			rose: styles.getPropertyValue('--chart-rose').trim(),
			roseFill: styles.getPropertyValue('--chart-rose-fill').trim(),
		};
	});

	// Chart data
	let sentimentChartData = $derived({
		labels: data.sentiment.arc.map((p) => p.position),
		datasets: [{
			label: 'Sentiment',
			data: data.sentiment.arc.map((p) => p.compound),
			borderColor: chartColors.blue,
			backgroundColor: chartColors.blueFill,
			fill: true, tension: 0.3, pointRadius: 0
		}]
	});

	let mattrChartData = $derived({
		labels: data.analysis.blocks.map((b) => b.id),
		datasets: [{
			label: 'MATTR',
			data: data.analysis.blocks.map((b) => b.metrics.mattr),
			borderColor: chartColors.green,
			backgroundColor: chartColors.greenFill,
			fill: true, tension: 0.3, pointRadius: 0
		}]
	});

	let chapterWordCountData = $derived({
		labels: data.chapters.chapters.map((c) => c.title),
		datasets: [{
			label: 'Word count',
			data: data.chapters.chapters.map((c) => c.word_count),
			backgroundColor: chartColors.amberFill,
			borderColor: chartColors.amber,
			borderWidth: 1
		}]
	});

	// Verb domain comparison: one dataset per character, grouped by domain
	let characterNames = $derived(Object.keys(data.characters.characters));
	let allVerbDomains = $derived(() => {
		const domains = new Set<string>();
		for (const profile of Object.values(data.characters.characters)) {
			for (const domain of Object.keys(profile.verb_domains)) {
				domains.add(domain);
			}
		}
		return [...domains].sort();
	});
	let domainColorPalette = $derived([chartColors.blue, chartColors.rose, chartColors.green, chartColors.amber]);
	let verbDomainChartData = $derived({
		labels: allVerbDomains(),
		datasets: characterNames.map((name, i) => ({
			label: name,
			data: allVerbDomains().map((d) => data.characters.characters[name].verb_domains[d] ?? 0),
			backgroundColor: domainColorPalette[i % domainColorPalette.length],
		}))
	});

	// Notables — resolve block references
	let longestSentenceBlock = $derived(data.analysis.notable.longest_sentences[0]
		? data.analysis.blocks.find((b) => b.id === data.analysis.notable.longest_sentences[0])
		: null);

	let richestBlock = $derived(data.analysis.notable.highest_mattr[0]
		? data.analysis.blocks.find((b) => b.id === data.analysis.notable.highest_mattr[0])
		: null);

	let foggiestChapter = $derived(() => {
		const ids = data.analysis.notable.highest_fog;
		if (!ids.length) return null;
		const block = data.analysis.blocks.find((b) => b.id === ids[0]);
		if (!block || block.chapter == null) return null;
		return data.chapters.chapters.find((c) => c.number === block.chapter) ?? null;
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
		<MetricCard label="Dialogue" value={avgDialogue} subtitle="avg ratio" />
	</div>

	<div class="charts-row">
		<a href="/{slug}/blocks" class="chart-container card chart-link">
			<h3>Sentiment Arc</h3>
			<MiniChart data={sentimentChartData} label="Sentiment arc across the text" />
		</a>
		<a href="/{slug}/blocks" class="chart-container card chart-link">
			<h3>Vocabulary Richness (MATTR)</h3>
			<MiniChart data={mattrChartData} label="MATTR per block across the text" />
		</a>
		<a href="/{slug}/chapters" class="chart-container card chart-link">
			<h3>Chapter Word Counts</h3>
			<MiniChart data={chapterWordCountData} type="bar" label="Word count per chapter" />
		</a>
		<a href="/{slug}/characters" class="chart-container card chart-link">
			<h3>Character Verb Domains</h3>
			<MiniChart data={verbDomainChartData} type="bar" label="Verb domain comparison across characters" />
		</a>
	</div>

	{#if longestSentenceBlock || richestBlock || foggiestChapter()}
		<div class="notables card">
			<h3>Notable</h3>
			<div class="notable-items">
				{#if longestSentenceBlock}
					<a href="/{slug}/blocks" class="notable-item">
						<span class="notable-label">Longest sentences</span>
						<span class="notable-value">Block {longestSentenceBlock.id}</span>
						<span class="notable-detail">{longestSentenceBlock.metrics.max_sentence_length} words — <em>"{longestSentenceBlock.longest_sentence_preview ?? longestSentenceBlock.preview}"</em></span>
					</a>
				{/if}
				{#if richestBlock}
					<a href="/{slug}/blocks" class="notable-item">
						<span class="notable-label">Richest vocabulary</span>
						<span class="notable-value">Block {richestBlock.id}</span>
						<span class="notable-detail">MATTR {richestBlock.metrics.mattr.toFixed(3)} — <em>"{richestBlock.preview}"</em></span>
					</a>
				{/if}
				{#if foggiestChapter()}
					<a href="/{slug}/chapters" class="notable-item">
						<span class="notable-label">Most complex chapter</span>
						<span class="notable-value">{foggiestChapter()!.title}</span>
						<span class="notable-detail">Fog index {foggiestChapter()!.fog.toFixed(1)}</span>
					</a>
				{/if}
			</div>
		</div>
	{/if}

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

	.chart-link {
		text-decoration: none;
		color: inherit;
		transition: box-shadow 0.15s;
	}

	.chart-link:hover {
		box-shadow: 0 2px 8px var(--shadow);
	}

	.chart-container h3 {
		font-size: 0.95rem;
		margin-bottom: 0.5rem;
		color: var(--text-secondary);
	}

	.notables h3,
	.pacing-section h3,
	.extremes h3 {
		font-size: 0.95rem;
		margin-bottom: 0.75rem;
		color: var(--text-secondary);
	}

	.notable-items {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.notable-item {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
		padding: 0.5rem 0.75rem;
		border-radius: var(--radius);
		text-decoration: none;
		color: inherit;
		transition: background 0.15s;
	}

	.notable-item:hover {
		background: var(--bg-secondary);
	}

	.notable-label {
		font-size: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: var(--text-muted);
	}

	.notable-value {
		font-family: var(--font-mono);
		font-size: 0.9rem;
		color: var(--accent);
	}

	.notable-detail {
		font-size: 0.85rem;
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
