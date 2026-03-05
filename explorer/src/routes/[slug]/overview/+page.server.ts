import { loadAllData } from '$lib/server/data';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params }) => {
	const data = await loadAllData(params.slug);
	return data;
};
