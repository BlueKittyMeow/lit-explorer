<script lang="ts">
	import type { AnalysisSummary } from '$lib/types/analysis';

	let { analysis }: {
		analysis: AnalysisSummary;
	} = $props();

	function relativeTime(dateStr: string): string {
		const now = Date.now();
		const then = new Date(dateStr).getTime();
		const diffMs = now - then;
		const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
		const diffDays = Math.floor(diffHours / 24);

		if (diffHours < 1) return 'just now';
		if (diffHours < 24) return `${diffHours}h ago`;
		if (diffDays < 30) return `${diffDays}d ago`;
		return new Date(dateStr).toLocaleDateString();
	}
</script>

<a href="/{analysis.slug}/overview" class="analysis-card card">
	<h2 class="card-title">{analysis.title}</h2>
	<div class="card-stats mono">
		<span>{analysis.word_count.toLocaleString()} words</span>
		<span class="separator">·</span>
		<span>{analysis.chapter_count} chapters</span>
		<span class="separator">·</span>
		<span>{analysis.analyzers_run.length} analyzers</span>
	</div>
	<div class="card-characters">
		{#each analysis.character_list as name}
			<span class="chip">{name}</span>
		{/each}
	</div>
	<time class="card-time" datetime={analysis.analyzed_at}>
		{relativeTime(analysis.analyzed_at)}
	</time>
</a>

<style>
	.analysis-card {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		text-decoration: none;
		color: inherit;
		transition: box-shadow 0.15s, border-color 0.15s;
	}

	.analysis-card:hover {
		border-color: var(--accent);
		box-shadow: 0 2px 8px var(--shadow);
		text-decoration: none;
	}

	.card-title {
		font-size: 1.2rem;
		color: var(--text-primary);
	}

	.card-stats {
		font-size: 0.85rem;
		color: var(--text-secondary);
	}

	.separator {
		margin: 0 0.25rem;
		color: var(--text-muted);
	}

	.card-characters {
		display: flex;
		gap: 0.35rem;
		flex-wrap: wrap;
	}

	.card-time {
		font-size: 0.75rem;
		color: var(--text-muted);
	}
</style>
