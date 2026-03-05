import { listAnalyses } from '$lib/server/data';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
	const analyses = await listAnalyses();
	return { analyses };
};
