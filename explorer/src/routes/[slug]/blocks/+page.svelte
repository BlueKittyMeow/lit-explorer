<script lang="ts">
	import { page } from '$app/state';
	import BlockReader from '$lib/components/BlockReader.svelte';
	import BlockMetricsPanel from '$lib/components/BlockMetricsPanel.svelte';
	import { resolveChartColors, onThemeChange } from '$lib/utils/chart-colors';
	import type { Block } from '$lib/types/analysis';
	import type ChartJS from 'chart.js/auto';

	let { data } = $props();
	let slug = $derived(page.params.slug);

	// Metric selector
	type MetricKey = 'mattr' | 'gunning_fog' | 'flesch_ease' | 'avg_sentence_length';
	const metricOptions: { key: MetricKey; label: string }[] = [
		{ key: 'mattr', label: 'MATTR' },
		{ key: 'gunning_fog', label: 'Fog' },
		{ key: 'flesch_ease', label: 'Flesch' },
		{ key: 'avg_sentence_length', label: 'Avg Sent Len' },
	];
	let selectedMetric = $state<MetricKey>('mattr');

	// Selected block — synced from ?from= query param, clamped to valid range
	let selectedBlockId = $state(1);

	// Sync from query param on navigation (handles chapter links → blocks page)
	$effect(() => {
		const from = page.url.searchParams.get('from');
		if (from) {
			const parsed = parseInt(from, 10);
			if (!isNaN(parsed) && data.analysis.blocks.some((b) => b.id === parsed)) {
				selectedBlockId = parsed;
			}
		}
	});

	let selectedBlock = $derived(
		data.analysis.blocks.find((b) => b.id === selectedBlockId) ?? data.analysis.blocks[0]
	);

	// Chapter title for selected block
	let selectedChapterTitle = $derived(() => {
		if (selectedBlock.chapter == null) return undefined;
		const ch = data.chapters.chapters.find((c) => c.number === selectedBlock.chapter);
		return ch?.title;
	});

	// Notable block IDs
	let notableBlockIds = $derived(new Set([
		...data.analysis.notable.longest_sentences,
		...data.analysis.notable.highest_mattr,
		...data.analysis.notable.highest_fog,
		...data.analysis.notable.shortest_sentences,
	]));

	// Chart colors — re-resolve on theme toggle via MutationObserver
	let chartColors = $state(resolveChartColors());
	$effect(() => {
		chartColors = resolveChartColors();
		return onThemeChange(() => { chartColors = resolveChartColors(); });
	});

	// Chart instance
	let canvas: HTMLCanvasElement;
	let chart: ChartJS | undefined;

	// Chapter boundary indices: find the first block index of each chapter transition
	let chapterBoundaryIndices = $derived(() => {
		const indices: number[] = [];
		const blocks = data.analysis.blocks;
		for (let i = 1; i < blocks.length; i++) {
			// Guard against null-chapter blocks
			if (blocks[i].chapter != null && blocks[i - 1].chapter != null &&
				blocks[i].chapter !== blocks[i - 1].chapter) {
				indices.push(i);
			}
		}
		return indices;
	});

	// Create/destroy chart
	$effect(() => {
		if (!canvas) return;

		const metric = selectedMetric;
		const colors = chartColors;
		const blocks = data.analysis.blocks;
		let cancelled = false;

		import('chart.js/auto').then(({ default: Chart }) => {
			if (cancelled) return;
			if (chart) chart.destroy();

			const pointColors = blocks.map((b) =>
				notableBlockIds.has(b.id) ? colors.rose : colors.blue
			);
			const pointRadii = blocks.map((b) =>
				b.id === selectedBlockId ? 6 : (notableBlockIds.has(b.id) ? 4 : 2)
			);

			// Custom plugin for chapter boundary lines
			const chapterBoundaryPlugin = {
				id: 'chapterBoundaries',
				afterDraw(chartInstance: ChartJS) {
					const ctx = chartInstance.ctx;
					const xScale = chartInstance.scales.x;
					const yScale = chartInstance.scales.y;
					if (!xScale || !yScale) return;

					ctx.save();
					ctx.strokeStyle = colors.amber;
					ctx.lineWidth = 1;
					ctx.setLineDash([4, 4]);

					for (const idx of chapterBoundaryIndices()) {
						const x = xScale.getPixelForValue(idx);
						ctx.beginPath();
						ctx.moveTo(x, yScale.top);
						ctx.lineTo(x, yScale.bottom);
						ctx.stroke();
					}

					ctx.restore();
				}
			};

			chart = new Chart(canvas, {
				type: 'line',
				data: {
					labels: blocks.map((b) => b.id),
					datasets: [{
						label: metricOptions.find((m) => m.key === metric)?.label ?? metric,
						data: blocks.map((b) => b.metrics[metric as keyof typeof b.metrics] as number),
						borderColor: colors.blue,
						backgroundColor: colors.blueFill,
						fill: true,
						tension: 0.3,
						pointBackgroundColor: pointColors,
						pointRadius: pointRadii,
					}]
				},
				options: {
					responsive: true,
					maintainAspectRatio: false,
					onClick(_event, elements) {
						if (elements.length > 0) {
							const idx = elements[0].index;
							selectedBlockId = blocks[idx].id;
						}
					},
					plugins: {
						legend: { display: false }
					},
					scales: {
						x: { title: { display: true, text: 'Block' } },
						y: { title: { display: true, text: metricOptions.find((m) => m.key === metric)?.label ?? metric } }
					}
				},
				plugins: [chapterBoundaryPlugin]
			});
		});

		return () => {
			cancelled = true;
			chart?.destroy();
			chart = undefined;
		};
	});

	// Update point styling on selection change (without full chart recreation)
	$effect(() => {
		if (!chart) return;
		const blocks = data.analysis.blocks;
		const id = selectedBlockId;

		const ds = chart.data.datasets[0];
		if (ds) {
			(ds as any).pointRadius = blocks.map((b: Block) =>
				b.id === id ? 6 : (notableBlockIds.has(b.id) ? 4 : 2)
			);
			(ds as any).pointBackgroundColor = blocks.map((b: Block) =>
				b.id === id ? chartColors.amber : (notableBlockIds.has(b.id) ? chartColors.rose : chartColors.blue)
			);
			chart.update('none');
		}
	});

	// Navigation
	function prevBlock() {
		const idx = data.analysis.blocks.findIndex((b) => b.id === selectedBlockId);
		if (idx > 0) selectedBlockId = data.analysis.blocks[idx - 1].id;
	}

	function nextBlock() {
		const idx = data.analysis.blocks.findIndex((b) => b.id === selectedBlockId);
		if (idx < data.analysis.blocks.length - 1) selectedBlockId = data.analysis.blocks[idx + 1].id;
	}

	// Keyboard navigation
	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'ArrowLeft') { prevBlock(); event.preventDefault(); }
		if (event.key === 'ArrowRight') { nextBlock(); event.preventDefault(); }
	}
</script>

<section class="block-explorer">
	<div class="metric-tabs">
		{#each metricOptions as opt}
			<button
				class="tab-pill"
				class:active={selectedMetric === opt.key}
				onclick={() => { selectedMetric = opt.key; }}
			>{opt.label}</button>
		{/each}
	</div>

	<!-- svelte-ignore a11y_no_noninteractive_tabindex a11y_no_noninteractive_element_interactions -->
	<div
		class="chart-area card"
		tabindex="0"
		role="application"
		aria-label="Block metric chart. Use arrow keys to navigate between blocks."
		onkeydown={handleKeydown}
	>
		<canvas bind:this={canvas}></canvas>
	</div>

	<div class="block-nav">
		<button onclick={prevBlock} disabled={selectedBlockId === data.analysis.blocks[0]?.id} aria-label="Previous block">
			&lt; Prev
		</button>
		<span class="block-indicator mono" aria-live="polite">
			Block {selectedBlock.id} of {data.analysis.total_blocks}
		</span>
		<button onclick={nextBlock} disabled={selectedBlockId === data.analysis.blocks[data.analysis.blocks.length - 1]?.id} aria-label="Next block">
			Next &gt;
		</button>
	</div>

	<div class="block-detail">
		<div class="detail-reader">
			<BlockReader block={selectedBlock} chapterTitle={selectedChapterTitle()} />
		</div>
		<div class="detail-metrics">
			<BlockMetricsPanel block={selectedBlock} notable={data.analysis.notable} />
		</div>
	</div>
</section>

<style>
	.block-explorer {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.metric-tabs {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.tab-pill {
		padding: 0.35rem 0.75rem;
		border: 1px solid var(--border);
		border-radius: var(--radius);
		background: var(--bg-card);
		color: var(--text-secondary);
		font-size: 0.8rem;
		cursor: pointer;
		transition: all 0.15s;
	}

	.tab-pill:hover {
		border-color: var(--accent);
		color: var(--accent);
	}

	.tab-pill.active {
		background: var(--accent);
		color: var(--bg-card);
		border-color: var(--accent);
	}

	.chart-area {
		height: 350px;
		position: relative;
	}

	.chart-area:focus {
		outline: 2px solid var(--accent);
		outline-offset: 2px;
	}

	.chart-area canvas {
		width: 100% !important;
		height: 100% !important;
	}

	.block-nav {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
	}

	.block-nav button {
		padding: 0.35rem 0.75rem;
		border: 1px solid var(--border);
		border-radius: var(--radius);
		background: var(--bg-card);
		color: var(--text-secondary);
		font-size: 0.85rem;
		cursor: pointer;
	}

	.block-nav button:hover:not(:disabled) {
		border-color: var(--accent);
		color: var(--accent);
	}

	.block-nav button:disabled {
		opacity: 0.4;
		cursor: default;
	}

	.block-indicator {
		font-size: 0.9rem;
		color: var(--text-secondary);
	}

	.block-detail {
		display: grid;
		grid-template-columns: 2fr 1fr;
		gap: 1rem;
	}

	@media (max-width: 768px) {
		.chart-area {
			height: 250px;
		}

		.block-detail {
			grid-template-columns: 1fr;
		}
	}
</style>
