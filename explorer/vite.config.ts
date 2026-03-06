import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	plugins: [sveltekit()],
	test: {
		include: ['tests/**/*.test.ts'],
		environment: 'jsdom',
		setupFiles: ['tests/setup.ts']
	},
	resolve: {
		// Required for Svelte 5 component tests (prevents server bundle resolution).
		// NOTE: This is global, not test-scoped. If you hit unexpected SSR import
		// errors in production, try scoping this to test config only.
		conditions: ['browser']
	}
});
