<script lang="ts">
	let { data } = $props();
</script>

<section class="placeholder card">
	<h2>Characters</h2>
	<p>Character agency analysis for <strong>{data.manifest.title}</strong>.</p>
	<p class="hint">Coming in Stage 6.</p>
</section>

<style>
	.placeholder {
		text-align: center;
		padding: 3rem;
		color: var(--text-secondary);
	}

	.hint {
		font-size: 0.85rem;
		color: var(--text-muted);
		margin-top: 0.5rem;
	}
</style>
