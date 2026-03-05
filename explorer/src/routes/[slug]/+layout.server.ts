import { loadManifest } from '$lib/server/data';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ params }) => {
	const manifest = await loadManifest(params.slug);
	return { manifest };
};
