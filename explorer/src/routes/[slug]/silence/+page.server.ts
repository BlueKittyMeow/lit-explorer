import { loadSilence, loadChapters } from '$lib/server/data';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, parent }) => {
	const { manifest } = await parent();
	const [silence, chapters] = await Promise.all([
		loadSilence(params.slug),
		loadChapters(params.slug)
	]);
	return { manifest, silence, chapters };
};
