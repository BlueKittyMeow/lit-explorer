<script lang="ts">
	import type { ChartData, ChartOptions, ChartType } from 'chart.js';
	import type ChartJS from 'chart.js/auto';

	let { data, type = 'line' as ChartType, options = {}, label = 'Chart' }: {
		data: ChartData;
		type?: ChartType;
		options?: ChartOptions;
		label?: string;
	} = $props();

	let canvas: HTMLCanvasElement;
	let chart: ChartJS | undefined;

	$effect(() => {
		if (!canvas) return;

		// Dynamic import avoids top-level chart.js/auto reference that crashes SSR
		import('chart.js/auto').then(({ default: Chart }) => {
			if (chart) {
				chart.destroy();
			}

			chart = new Chart(canvas, {
				type,
				data,
				options: {
					responsive: true,
					maintainAspectRatio: false,
					...options
				}
			});
		});

		return () => {
			chart?.destroy();
			chart = undefined;
		};
	});
</script>

<figure class="mini-chart" role="img" aria-label={label}>
	<canvas bind:this={canvas}></canvas>
	<figcaption class="sr-only">
		{label}: {data.datasets?.[0]?.data?.length ?? 0} data points
	</figcaption>
</figure>

<style>
	.mini-chart {
		position: relative;
		height: 160px;
		width: 100%;
	}

	canvas {
		width: 100% !important;
		height: 100% !important;
	}
</style>
