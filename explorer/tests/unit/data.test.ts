/**
 * Tests for the data loading layer ($lib/server/data.ts).
 *
 * These tests use the fixture data in tests/fixtures/test-analysis/
 * and mock $env/dynamic/private to set ANALYSES_DIR.
 */

import { describe, it, expect, vi, beforeAll } from 'vitest';
import { resolve } from 'node:path';

const FIXTURES_DIR = resolve(import.meta.dirname, '..', 'fixtures');

// Mock SvelteKit's $env/dynamic/private
vi.mock('$env/dynamic/private', () => ({
	env: { ANALYSES_DIR: resolve(import.meta.dirname, '..', 'fixtures') }
}));

// Mock @sveltejs/kit error() to throw like it does at runtime
vi.mock('@sveltejs/kit', () => ({
	error: (status: number, message: string) => {
		const err = new Error(message);
		(err as any).status = status;
		throw err;
	}
}));

async function getLoaders() {
	return await import('../../src/lib/server/data.js');
}

describe('listAnalyses', () => {
	it('returns summaries from fixture directory', async () => {
		const { listAnalyses } = await getLoaders();
		const list = await listAnalyses();
		expect(list).toHaveLength(1);
		expect(list[0].slug).toBe('test-analysis');
		expect(list[0].title).toBe('Test Manuscript');
		expect(list[0].word_count).toBe(5000);
		expect(list[0].chapter_count).toBe(2);
		expect(list[0].character_list).toEqual(['emil', 'felix']);
		expect(list[0].analyzers_run).toHaveLength(8);
	});

	it('returns empty array for nonexistent directory', async () => {
		const envMod = await import('$env/dynamic/private');
		const origDir = envMod.env.ANALYSES_DIR;
		envMod.env.ANALYSES_DIR = '/tmp/nonexistent-lit-explorer-test';
		try {
			const { listAnalyses } = await getLoaders();
			const list = await listAnalyses();
			expect(list).toEqual([]);
		} finally {
			envMod.env.ANALYSES_DIR = origDir;
		}
	});
});

describe('loadManifest', () => {
	it('returns typed manifest with warnings field', async () => {
		const { loadManifest } = await getLoaders();
		const manifest = await loadManifest('test-analysis');
		expect(manifest.title).toBe('Test Manuscript');
		expect(manifest.slug).toBe('test-analysis');
		expect(manifest.warnings).toEqual([]);
		expect(manifest.engine_version).toBe('0.1.0');
	});

	it('throws 404 for missing slug', async () => {
		const { loadManifest } = await getLoaders();
		await expect(loadManifest('nonexistent')).rejects.toThrow();
	});
});

describe('loadAnalysis', () => {
	it('loads analysis with pacing data', async () => {
		const { loadAnalysis } = await getLoaders();
		const analysis = await loadAnalysis('test-analysis');
		expect(analysis.total_blocks).toBe(5);
		expect(analysis.notable.longest_sentences).toEqual([1, 3]);
		expect(analysis.pacing?.distribution.mean).toBe(18.3);
	});
});

describe('loadCharacters', () => {
	it('loads character profiles', async () => {
		const { loadCharacters } = await getLoaders();
		const chars = await loadCharacters('test-analysis');
		expect(chars.characters.felix.verb_domains.cognition).toBe(18);
	});
});

describe('loadChapters', () => {
	it('loads chapters without block_to_chapter', async () => {
		const { loadChapters } = await getLoaders();
		const chapters = await loadChapters('test-analysis');
		expect(chapters.chapters).toHaveLength(2);
		expect(chapters.chapters[0].sentiment.neu).toBe(0.88);
		// block_to_chapter is NOT in the file
		expect((chapters as unknown as Record<string, unknown>).block_to_chapter).toBeUndefined();
	});
});

describe('loadSentiment', () => {
	it('loads sentiment with smoothed_arc', async () => {
		const { loadSentiment } = await getLoaders();
		const sentiment = await loadSentiment('test-analysis');
		expect(sentiment.method).toBe('vader');
		expect(sentiment.smoothed_arc).toHaveLength(3);
		expect(sentiment.arc[0].neu).toBe(0.90);
	});
});

describe('loadSilence', () => {
	it('loads silence data with gaps', async () => {
		const { loadSilence } = await getLoaders();
		const silence = await loadSilence('test-analysis');
		expect(silence.total_gaps).toBe(4);
		expect(silence.gaps).toHaveLength(4);
		expect(silence.longest_silence).not.toBeNull();
		expect(silence.longest_silence!.word_count).toBe(210);
		expect(silence.avg_gap_words).toBe(102.5);
	});
});

describe('path traversal guard', () => {
	it('rejects slug with ..', async () => {
		const { loadManifest } = await getLoaders();
		await expect(loadManifest('../etc/passwd')).rejects.toThrow();
	});

	it('rejects slug with /', async () => {
		const { loadManifest } = await getLoaders();
		await expect(loadManifest('foo/bar')).rejects.toThrow();
	});

	it('rejects slug starting with hyphen', async () => {
		const { loadManifest } = await getLoaders();
		await expect(loadManifest('-bad-slug')).rejects.toThrow();
	});

	it('rejects slug with uppercase', async () => {
		const { loadManifest } = await getLoaders();
		await expect(loadManifest('BadSlug')).rejects.toThrow();
	});

	it('rejects encoded traversal', async () => {
		const { loadManifest } = await getLoaders();
		await expect(loadManifest('%2e%2e')).rejects.toThrow();
	});
});

describe('slug from accented title', () => {
	it('loads fixture with accented chapter title correctly', async () => {
		const { loadChapters } = await getLoaders();
		const chapters = await loadChapters('test-analysis');
		// The chapter title contains an accent (Café Union)
		expect(chapters.chapters[0].title).toBe('Café Union');
	});
});
