<script lang="ts">
	import { onMount } from 'svelte';
	import Chart from 'chart.js/auto';
	import type { ChartData, ChartOptions, ChartType } from 'chart.js';

	let { data, type = 'line' as ChartType, options = {}, label = 'Chart' }: {
		data: ChartData;
		type?: ChartType;
		options?: ChartOptions;
		label?: string;
	} = $props();

	let canvas: HTMLCanvasElement;

	onMount(() => {
		const chart = new Chart(canvas, {
			type,
			data,
			options: {
				responsive: true,
				maintainAspectRatio: false,
				...options
			}
		});
		return () => chart.destroy();
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
