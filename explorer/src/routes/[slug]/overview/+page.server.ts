import { loadAnalysis, loadCharacters, loadChapters, loadSentiment } from '$lib/server/data';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, parent }) => {
	// Manifest already loaded by [slug]/+layout.server.ts — reuse it
	const { manifest } = await parent();
	const [analysis, characters, chapters, sentiment] = await Promise.all([
		loadAnalysis(params.slug),
		loadCharacters(params.slug),
		loadChapters(params.slug),
		loadSentiment(params.slug)
	]);
	return { manifest, analysis, characters, chapters, sentiment };
};
