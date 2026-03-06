import { loadCharacters } from '$lib/server/data';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, parent }) => {
	const { manifest } = await parent();
	const characters = await loadCharacters(params.slug);
	return { manifest, characters };
};
