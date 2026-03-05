<script lang="ts">
	import AnalysisCard from '$lib/components/AnalysisCard.svelte';

	let { data } = $props();
</script>

<div class="landing">
	<h1>Analyses</h1>

	{#if data.analyses.length === 0}
		<div class="empty-state card">
			<p>No analyses found.</p>
			<p class="hint">Run <code>lit-engine analyze &lt;file&gt;</code> to generate one.</p>
		</div>
	{:else}
		<div class="analysis-grid">
			{#each data.analyses as analysis (analysis.slug)}
				<AnalysisCard {analysis} />
			{/each}
		</div>
	{/if}
</div>

<style>
	.landing h1 {
		font-family: var(--font-serif);
		margin-bottom: 1.5rem;
	}

	.analysis-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
		gap: 1rem;
	}

	.empty-state {
		text-align: center;
		padding: 3rem;
		color: var(--text-secondary);
	}

	.hint {
		margin-top: 0.5rem;
		font-size: 0.85rem;
		color: var(--text-muted);
	}

	.hint code {
		font-family: var(--font-mono);
		background: var(--bg-secondary);
		padding: 0.15rem 0.4rem;
		border-radius: 3px;
	}
</style>
