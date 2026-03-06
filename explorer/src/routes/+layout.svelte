<script lang="ts">
	import '../app.css';

	type ThemePref = 'light' | 'dark' | 'system';
	const THEME_LABELS: Record<ThemePref, string> = { light: 'Light', dark: 'Dark', system: 'System' };
	const THEME_CYCLE: Record<ThemePref, ThemePref> = { light: 'dark', dark: 'system', system: 'light' };

	let { children } = $props();
	let themePref = $state<ThemePref>('system');

	function applyTheme(pref: ThemePref) {
		const isDark = pref === 'dark' || (pref === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
		document.documentElement.classList.toggle('dark', isDark);
	}

	function cycleTheme() {
		themePref = THEME_CYCLE[themePref];
		localStorage.setItem('theme', themePref);
		applyTheme(themePref);
	}

	$effect(() => {
		const stored = localStorage.getItem('theme') as ThemePref | null;
		themePref = stored && stored in THEME_LABELS ? stored : 'system';
		applyTheme(themePref);

		// Listen for OS theme changes when in system mode
		const mql = window.matchMedia('(prefers-color-scheme: dark)');
		const handler = () => { if (themePref === 'system') applyTheme('system'); };
		mql.addEventListener('change', handler);
		return () => mql.removeEventListener('change', handler);
	});
</script>

<svelte:head>
	<title>Lit Explorer</title>
</svelte:head>

<div class="app-shell">
	<header class="top-bar">
		<a href="/" class="brand">Lit Explorer</a>
		<button class="theme-toggle" onclick={cycleTheme} aria-label="Theme: {THEME_LABELS[themePref]}. Click to cycle.">
			{THEME_LABELS[themePref]}
		</button>
	</header>

	<main class="main-content">
		{@render children()}
	</main>
</div>

<style>
	.app-shell {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
	}

	.top-bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem 1.5rem;
		border-bottom: 1px solid var(--border);
		background: var(--bg-primary);
		position: sticky;
		top: 0;
		z-index: 10;
	}

	.brand {
		font-family: var(--font-serif);
		font-size: 1.2rem;
		font-weight: 600;
		color: var(--text-primary);
		text-decoration: none;
	}

	.theme-toggle {
		padding: 0.35rem 0.75rem;
		border: 1px solid var(--border);
		border-radius: 4px;
		background: var(--bg-secondary);
		color: var(--text-secondary);
		cursor: pointer;
		font-size: 0.8rem;
	}

	.theme-toggle:hover {
		border-color: var(--accent);
	}

	.main-content {
		flex: 1;
		padding: 2rem 1.5rem;
		max-width: 1200px;
		margin: 0 auto;
		width: 100%;
	}
</style>
