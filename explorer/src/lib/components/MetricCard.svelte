<script lang="ts">
	let { label, value, subtitle = '' }: {
		label: string;
		value: string | number;
		subtitle?: string;
	} = $props();
</script>

<div class="metric-card card">
	<span class="metric-label">{label}</span>
	<span class="metric-value mono">{value}</span>
	{#if subtitle}
		<span class="metric-subtitle">{subtitle}</span>
	{/if}
</div>

<style>
	.metric-card {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		min-width: 140px;
	}

	.metric-label {
		font-size: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--text-muted);
	}

	.metric-value {
		font-size: 1.5rem;
		font-weight: 600;
		color: var(--text-primary);
	}

	.metric-subtitle {
		font-size: 0.8rem;
		color: var(--text-secondary);
	}
</style>
