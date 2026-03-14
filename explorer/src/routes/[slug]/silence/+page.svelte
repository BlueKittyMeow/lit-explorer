<script lang="ts">
	import MetricCard from '$lib/components/MetricCard.svelte';
	import { resolveChartColors, onThemeChange } from '$lib/utils/chart-colors';
	import { exportChartAsPng } from '$lib/utils/chart-export';
	import type ChartJS from 'chart.js/auto';

	let { data } = $props();

	// Chart colors — re-resolve on theme toggle
	let chartColors = $state(resolveChartColors());
	$effect(() => {
		chartColors = resolveChartColors();
		return onThemeChange(() => { chartColors = resolveChartColors(); });
	});

	// Chart instance
	let canvas: HTMLCanvasElement;
	let chart: ChartJS | undefined;

	// Longest gap index for highlighting
	let longestGapIndex = $derived(() => {
		if (data.silence.gaps.length === 0) return -1;
		let maxIdx = 0;
		for (let i = 1; i < data.silence.gaps.length; i++) {
			if (data.silence.gaps[i].word_count > data.silence.gaps[maxIdx].word_count) {
				maxIdx = i;
			}
		}
		return maxIdx;
	});

	// Create/destroy chart
	$effect(() => {
		if (!canvas) return;

		const gaps = data.silence.gaps;
		const colors = chartColors;
		let cancelled = false;

		import('chart.js/auto').then(({ default: Chart }) => {
			if (cancelled) return;
			if (chart) chart.destroy();

			const longestIdx = longestGapIndex();
			const barColors = gaps.map((_, i) =>
				i === longestIdx ? colors.rose : colors.blue
			);

			chart = new Chart(canvas, {
				type: 'bar',
				data: {
					labels: gaps.map((_, i) => `Gap ${i + 1}`),
					datasets: [{
						label: 'Words',
						data: gaps.map((g) => g.word_count),
						backgroundColor: barColors,
						borderColor: barColors,
						borderWidth: 1,
					}]
				},
				options: {
					responsive: true,
					maintainAspectRatio: false,
					plugins: {
						legend: { display: false }
					},
					scales: {
						x: { title: { display: true, text: 'Silence Gap' } },
						y: { title: { display: true, text: 'Word Count' } }
					}
				}
			});
		});

		return () => {
			cancelled = true;
			chart?.destroy();
			chart = undefined;
		};
	});
</script>

<section class="silence-page">
	<div class="metric-row">
		<MetricCard label="Total Gaps" value={data.silence.total_gaps} />
		<MetricCard label="Avg Gap Words" value={data.silence.avg_gap_words} />
		<MetricCard label="Longest Silence" value={data.silence.longest_silence?.word_count ?? 0} />
	</div>

	<div class="chart-header">
		<button
			class="export-btn"
			onclick={() => exportChartAsPng(chart, 'silence-gaps.png')}
			disabled={!chart}
			aria-label="Export chart as PNG"
		>Export PNG</button>
	</div>

	<figure class="chart-area card" role="img" aria-label="Silence gaps bar chart showing word count per gap">
		<canvas bind:this={canvas}></canvas>
		<figcaption class="sr-only">
			Bar chart showing {data.silence.total_gaps} silence gaps between dialogue
		</figcaption>
	</figure>

	{#if data.silence.longest_silence}
		<div class="longest-callout card">
			<h3>Longest Silence</h3>
			<p class="callout-meta mono">
				{data.silence.longest_silence.word_count} words · Position: {(data.silence.longest_silence.position * 100).toFixed(0)}% through text
			</p>
			<blockquote class="callout-preview">
				{data.silence.longest_silence.preview}
			</blockquote>
		</div>
	{/if}
</section>

<style>
	.silence-page {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.metric-row {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
		gap: 1rem;
	}

	.chart-header {
		display: flex;
		justify-content: flex-end;
	}

	.export-btn {
		padding: 0.35rem 0.75rem;
		border: 1px solid var(--border);
		border-radius: var(--radius);
		background: var(--bg-card);
		color: var(--text-secondary);
		font-size: 0.8rem;
		cursor: pointer;
		transition: all 0.15s;
	}

	.export-btn:hover:not(:disabled) {
		border-color: var(--accent);
		color: var(--accent);
	}

	.export-btn:disabled {
		opacity: 0.4;
		cursor: default;
	}

	.chart-area {
		height: 300px;
		position: relative;
	}

	.chart-area canvas {
		width: 100% !important;
		height: 100% !important;
	}

	.longest-callout {
		padding: 1.25rem;
	}

	.longest-callout h3 {
		margin: 0 0 0.5rem;
		font-size: 1rem;
		color: var(--text-primary);
	}

	.callout-meta {
		font-size: 0.85rem;
		color: var(--text-secondary);
		margin: 0 0 0.75rem;
	}

	.callout-preview {
		font-family: var(--font-serif);
		font-size: 0.95rem;
		line-height: 1.6;
		color: var(--text-primary);
		border-left: 3px solid var(--accent);
		padding-left: 1rem;
		margin: 0;
	}

	@media (max-width: 768px) {
		.chart-area {
			height: 200px;
		}
	}
</style>
