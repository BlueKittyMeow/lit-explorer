<script lang="ts">
	import CharacterCard from '$lib/components/CharacterCard.svelte';
	import VerbDomainChart from '$lib/components/VerbDomainChart.svelte';
	import { resolveChartColors, chartPalette } from '$lib/utils/chart-colors';

	let { data } = $props();

	let chartColors = $state(resolveChartColors());

	$effect(() => {
		chartColors = resolveChartColors();
	});

	// All character names
	let characterNames = $derived(Object.keys(data.characters.characters));

	// Verb domain comparison chart: all characters grouped by domain
	let allDomains = $derived(() => {
		const domains = new Set<string>();
		for (const profile of Object.values(data.characters.characters)) {
			for (const domain of Object.keys(profile.verb_domains)) {
				domains.add(domain);
			}
		}
		return [...domains].sort();
	});

	let palette = $derived(chartPalette(chartColors));
	let comparisonChartData = $derived({
		labels: allDomains(),
		datasets: characterNames.map((name, i) => ({
			label: name,
			data: allDomains().map((d) => data.characters.characters[name].verb_domains[d] ?? 0),
			backgroundColor: palette[i % palette.length],
		}))
	});
</script>

<section class="characters">
	<div class="character-grid">
		{#each characterNames as name (name)}
			<CharacterCard {name} profile={data.characters.characters[name]} />
		{/each}
	</div>

	{#if characterNames.length > 1}
		<div class="comparison card">
			<h3>Verb Domain Comparison</h3>
			<VerbDomainChart
				data={comparisonChartData}
				label="Verb domain comparison across characters"
				height={300}
			/>
		</div>
	{/if}
</section>

<style>
	.characters {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.character-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
		gap: 1rem;
	}

	.comparison h3 {
		font-size: 0.95rem;
		margin-bottom: 0.75rem;
		color: var(--text-secondary);
	}

	@media (max-width: 480px) {
		.character-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
