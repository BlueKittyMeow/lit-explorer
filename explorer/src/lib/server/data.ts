/**
 * Server-only data loading layer for analysis JSON files.
 * Reads from ANALYSES_DIR (env) or defaults to ../shared/analyses/ relative to cwd.
 */

import { readdir, readFile } from 'node:fs/promises';
import { resolve, sep } from 'node:path';
import { error } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import type {
	Manifest,
	Analysis,
	Characters,
	Chapters,
	Sentiment,
	Silence,
	AnalysisSummary,
} from '$lib/types/analysis';

const SLUG_PATTERN = /^[a-z0-9][a-z0-9_-]*$/;

function getAnalysesDir(): string {
	return env.ANALYSES_DIR || resolve(process.cwd(), '..', 'shared', 'analyses');
}

function validateSlug(slug: string): void {
	if (!SLUG_PATTERN.test(slug)) {
		error(400, `Invalid analysis slug: "${slug}"`);
	}
	const base = resolve(getAnalysesDir());
	const candidate = resolve(base, slug);
	if (candidate !== base && !candidate.startsWith(base + sep)) {
		error(400, 'Invalid analysis path');
	}
}

async function readJson<T>(slug: string, filename: string): Promise<T> {
	validateSlug(slug);
	const filePath = resolve(getAnalysesDir(), slug, filename);
	try {
		const content = await readFile(filePath, 'utf-8');
		return JSON.parse(content) as T;
	} catch (err) {
		if ((err as NodeJS.ErrnoException).code === 'ENOENT') {
			error(404, `Analysis file not found: ${slug}/${filename}`);
		}
		throw err;
	}
}

export async function listAnalyses(): Promise<AnalysisSummary[]> {
	const dir = getAnalysesDir();
	let entries: string[];
	try {
		entries = await readdir(dir);
	} catch {
		return [];
	}

	const summaries: AnalysisSummary[] = [];
	for (const entry of entries) {
		if (!SLUG_PATTERN.test(entry)) continue;
		try {
			const manifest = await readJson<Manifest>(entry, 'manifest.json');
			summaries.push({
				slug: entry,
				title: manifest.title,
				word_count: manifest.word_count,
				chapter_count: manifest.chapter_count,
				character_list: manifest.character_list,
				analyzed_at: manifest.analyzed_at,
				analyzers_run: manifest.analyzers_run
			});
		} catch (err) {
			console.warn(`[lit-explorer] Skipping analysis "${entry}": failed to read manifest`, err);
		}
	}

	// Newest first
	summaries.sort((a, b) => b.analyzed_at.localeCompare(a.analyzed_at));
	return summaries;
}

export async function loadManifest(slug: string): Promise<Manifest> {
	return readJson<Manifest>(slug, 'manifest.json');
}

export async function loadAnalysis(slug: string): Promise<Analysis> {
	return readJson<Analysis>(slug, 'analysis.json');
}

export async function loadCharacters(slug: string): Promise<Characters> {
	return readJson<Characters>(slug, 'characters.json');
}

export async function loadChapters(slug: string): Promise<Chapters> {
	return readJson<Chapters>(slug, 'chapters.json');
}

export async function loadSentiment(slug: string): Promise<Sentiment> {
	return readJson<Sentiment>(slug, 'sentiment.json');
}

export async function loadSilence(slug: string): Promise<Silence> {
	return readJson<Silence>(slug, 'silence.json');
}
