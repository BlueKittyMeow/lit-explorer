<script lang="ts">
	import type { CharacterProfile } from '$lib/types/analysis';

	let { name, profile }: { name: string; profile: CharacterProfile } = $props();

	// Active/passive percentages (of total_verbs)
	let activePercent = $derived(
		profile.total_verbs > 0
			? Math.round((profile.active_count / profile.total_verbs) * 100)
			: 0
	);
	let passivePercent = $derived(100 - activePercent);

	// Via name/pronoun ratio
	// Note: via_name + via_pronoun can exceed total_verbs because some verbs
	// are attributed both by name and by pronoun. We use the sum as denominator.
	let attributionTotal = $derived(profile.via_name + profile.via_pronoun);
	let namePercent = $derived(
		attributionTotal > 0
			? Math.round((profile.via_name / attributionTotal) * 100)
			: 0
	);
	let pronounPercent = $derived(100 - namePercent);
</script>

<div class="character-card card">
	<h3 class="character-name">{name}</h3>

	<div class="stat-row">
		<span class="stat-label">Total verbs</span>
		<span class="stat-value mono">{profile.total_verbs}</span>
	</div>

	<div class="bar-section">
		<span class="bar-label">Active / Passive</span>
		<div class="split-bar">
			<div class="bar-fill active" style="width: {activePercent}%"></div>
			<div class="bar-fill passive" style="width: {passivePercent}%"></div>
		</div>
		<span class="bar-legend mono">{activePercent}% active · {passivePercent}% passive</span>
	</div>

	<div class="bar-section">
		<span class="bar-label">Attribution</span>
		<div class="split-bar">
			<div class="bar-fill name-ref" style="width: {namePercent}%"></div>
			<div class="bar-fill pronoun-ref" style="width: {pronounPercent}%"></div>
		</div>
		<span class="bar-legend mono">{namePercent}% by name · {pronounPercent}% by pronoun</span>
	</div>

	{#if profile.top_verbs.length > 0}
		<div class="list-section">
			<h4>Top Verbs</h4>
			<div class="verb-list">
				{#each profile.top_verbs as entry}
					<span class="verb-item">
						<span class="verb-text">{entry.verb}</span>
						<span class="verb-count mono">{entry.count}</span>
						{#if entry.category}
							<span class="chip">{entry.category}</span>
						{/if}
					</span>
				{/each}
			</div>
		</div>
	{/if}

	{#if profile.top_actions.length > 0}
		<div class="list-section">
			<h4>Top Actions</h4>
			<div class="verb-list">
				{#each profile.top_actions as entry}
					<span class="verb-item">
						<span class="verb-text">{entry.action}</span>
						<span class="verb-count mono">{entry.count}</span>
					</span>
				{/each}
			</div>
		</div>
	{/if}

	{#if profile.passive_count > 0}
		<div class="list-section">
			<h4>Passive</h4>
			{#if profile.passive_verbs.length > 0}
				<div class="verb-list">
					{#each profile.passive_verbs as entry}
						<span class="verb-item">
							<span class="verb-text">{entry.verb}</span>
							<span class="verb-count mono">{entry.count}</span>
						</span>
					{/each}
				</div>
			{/if}
			{#if profile.passive_agents.length > 0}
				<div class="agents">
					<span class="bar-label">Agents</span>
					{#each profile.passive_agents as agent}
						<span class="chip">{agent.agent}</span>
					{/each}
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.character-card {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.character-name {
		font-size: 1.15rem;
		text-transform: capitalize;
		color: var(--accent);
	}

	.stat-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.stat-label {
		font-size: 0.8rem;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	.stat-value {
		font-size: 1.1rem;
		color: var(--text-primary);
	}

	.bar-section {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.bar-label {
		font-size: 0.75rem;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	.split-bar {
		display: flex;
		height: 8px;
		border-radius: 4px;
		overflow: hidden;
		background: var(--bg-secondary);
	}

	.bar-fill.active { background: var(--chart-blue); }
	.bar-fill.passive { background: var(--chart-rose); }
	.bar-fill.name-ref { background: var(--chart-green); }
	.bar-fill.pronoun-ref { background: var(--chart-amber); }

	.bar-legend {
		font-size: 0.75rem;
		color: var(--text-secondary);
	}

	.list-section h4 {
		font-size: 0.8rem;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.04em;
		margin-bottom: 0.25rem;
	}

	.verb-list {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.verb-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.85rem;
	}

	.verb-text {
		color: var(--text-primary);
	}

	.verb-count {
		font-size: 0.8rem;
		color: var(--text-secondary);
	}

	.agents {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-top: 0.25rem;
	}
</style>
