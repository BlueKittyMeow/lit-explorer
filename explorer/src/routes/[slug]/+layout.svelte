<script lang="ts">
	import { page } from '$app/state';

	let { data, children } = $props();
	let slug = $derived(page.params.slug);

	// Extract current sub-page from pathname, stripping trailing slash
	let currentPage = $derived(page.url.pathname.replace(/\/$/, '').split('/').pop() ?? '');
</script>

<div class="analysis-layout">
	<nav class="sub-nav" aria-label="Analysis sections">
		<a href="/{slug}/overview" class:active={currentPage === 'overview'} aria-current={currentPage === 'overview' ? 'page' : undefined}>Overview</a>
		<a href="/{slug}/chapters" class:active={currentPage === 'chapters'} aria-current={currentPage === 'chapters' ? 'page' : undefined}>Chapters</a>
		<a href="/{slug}/characters" class:active={currentPage === 'characters'} aria-current={currentPage === 'characters' ? 'page' : undefined}>Characters</a>
		<a href="/{slug}/blocks" class:active={currentPage === 'blocks'} aria-current={currentPage === 'blocks' ? 'page' : undefined}>Blocks</a>
		<a href="/{slug}/silence" class:active={currentPage === 'silence'} aria-current={currentPage === 'silence' ? 'page' : undefined}>Silence</a>
	</nav>

	<header class="analysis-header">
		<h1>{data.manifest.title}</h1>
		<div class="analysis-meta mono">
			<span>{data.manifest.word_count.toLocaleString()} words</span>
			<span class="sep">·</span>
			<span>{data.manifest.chapter_count} chapters</span>
			<span class="sep">·</span>
			<span>{data.manifest.character_list.length} characters</span>
		</div>
	</header>

	{@render children()}
</div>

<style>
	.analysis-layout {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.sub-nav {
		display: flex;
		gap: 0.25rem;
		border-bottom: 1px solid var(--border);
		padding-bottom: 0.5rem;
	}

	.sub-nav a {
		padding: 0.4rem 0.8rem;
		border-radius: 4px 4px 0 0;
		border-bottom: 2px solid transparent;
		text-decoration: none;
		font-size: 0.9rem;
		color: var(--text-secondary);
		transition: color 0.15s, background 0.15s, border-color 0.15s;
	}

	.sub-nav a:hover {
		color: var(--text-primary);
		background: var(--bg-secondary);
	}

	.sub-nav a.active {
		color: var(--accent);
		border-bottom-color: var(--accent);
		font-weight: 500;
	}

	.analysis-header h1 {
		font-family: var(--font-serif);
		margin: 0;
	}

	.analysis-meta {
		font-size: 0.85rem;
		color: var(--text-secondary);
	}

	.sep {
		margin: 0 0.25rem;
		color: var(--text-muted);
	}
</style>
