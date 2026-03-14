<script lang="ts">
	import type { ChartData, ChartOptions } from 'chart.js';
	import type ChartJS from 'chart.js/auto';

	let { data, label = 'Verb domain chart', height = 200 }: {
		data: ChartData<'bar'>;
		label?: string;
		height?: number;
	} = $props();

	let canvas: HTMLCanvasElement;
	let chart: ChartJS | undefined;

	$effect(() => {
		if (!canvas) return;
		let cancelled = false;

		import('chart.js/auto').then(({ default: Chart }) => {
			if (cancelled) return;
			if (chart) {
				chart.destroy();
			}

			chart = new Chart(canvas, {
				type: 'bar',
				data,
				options: {
					indexAxis: 'y',
					responsive: true,
					maintainAspectRatio: false,
					plugins: {
						legend: { display: data.datasets.length > 1 }
					}
				} as ChartOptions<'bar'>
			});
		});

		return () => {
			cancelled = true;
			chart?.destroy();
			chart = undefined;
		};
	});
</script>

<figure class="verb-domain-chart" role="img" aria-label={label} style="height: {height}px">
	<canvas bind:this={canvas}></canvas>
	<figcaption class="sr-only">
		{label}: {data.labels?.length ?? 0} domains
	</figcaption>
</figure>

<style>
	.verb-domain-chart {
		position: relative;
		width: 100%;
	}

	canvas {
		width: 100% !important;
		height: 100% !important;
	}
</style>
