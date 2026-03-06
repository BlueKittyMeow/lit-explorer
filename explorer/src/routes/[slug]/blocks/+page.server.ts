import { loadAnalysis, loadChapters } from '$lib/server/data';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, parent }) => {
	const { manifest } = await parent();
	const [analysis, chapters] = await Promise.all([
		loadAnalysis(params.slug),
		loadChapters(params.slug)
	]);
	return { manifest, analysis, chapters };
};
