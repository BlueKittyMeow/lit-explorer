import { loadChapters } from '$lib/server/data';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, parent }) => {
	const { manifest } = await parent();
	const chapters = await loadChapters(params.slug);
	return { manifest, chapters };
};
