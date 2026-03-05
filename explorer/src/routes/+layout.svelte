<script lang="ts">
	import '../app.css';

	let { children } = $props();
	let darkMode = $state(false);

	function toggleTheme() {
		darkMode = !darkMode;
		document.documentElement.classList.toggle('dark', darkMode);
		localStorage.setItem('theme', darkMode ? 'dark' : 'light');
	}

	$effect(() => {
		darkMode = document.documentElement.classList.contains('dark');
	});
</script>

<svelte:head>
	<title>Lit Explorer</title>
</svelte:head>

<div class="app-shell">
	<header class="top-bar">
		<a href="/" class="brand">Lit Explorer</a>
		<button class="theme-toggle" onclick={toggleTheme} aria-label="Toggle theme">
			{darkMode ? 'Light' : 'Dark'}
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
