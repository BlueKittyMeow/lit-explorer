/**
 * Shared chart color utility — SSR-safe resolution of CSS variable chart colors.
 *
 * Provides deterministic fallback hex values for SSR (before `document` exists),
 * then resolves live CSS variables on the client via getComputedStyle.
 */

export interface ChartColorSet {
	blue: string;
	blueFill: string;
	green: string;
	greenFill: string;
	amber: string;
	amberFill: string;
	rose: string;
	roseFill: string;
}

/** Light-mode fallback values (match :root in app.css). */
const FALLBACK_COLORS: ChartColorSet = {
	blue: 'hsl(220, 50%, 55%)',
	blueFill: 'hsla(220, 50%, 55%, 0.1)',
	green: 'hsl(150, 45%, 45%)',
	greenFill: 'hsla(150, 45%, 45%, 0.1)',
	amber: 'hsl(35, 70%, 50%)',
	amberFill: 'hsla(35, 70%, 50%, 0.1)',
	rose: 'hsl(350, 55%, 55%)',
	roseFill: 'hsla(350, 55%, 55%, 0.1)',
};

/**
 * Resolve chart colors from CSS variables.
 * Returns deterministic fallbacks during SSR or when document is unavailable.
 */
export function resolveChartColors(): ChartColorSet {
	if (typeof document === 'undefined') return { ...FALLBACK_COLORS };

	const styles = getComputedStyle(document.documentElement);
	return {
		blue: styles.getPropertyValue('--chart-blue').trim() || FALLBACK_COLORS.blue,
		blueFill: styles.getPropertyValue('--chart-blue-fill').trim() || FALLBACK_COLORS.blueFill,
		green: styles.getPropertyValue('--chart-green').trim() || FALLBACK_COLORS.green,
		greenFill: styles.getPropertyValue('--chart-green-fill').trim() || FALLBACK_COLORS.greenFill,
		amber: styles.getPropertyValue('--chart-amber').trim() || FALLBACK_COLORS.amber,
		amberFill: styles.getPropertyValue('--chart-amber-fill').trim() || FALLBACK_COLORS.amberFill,
		rose: styles.getPropertyValue('--chart-rose').trim() || FALLBACK_COLORS.rose,
		roseFill: styles.getPropertyValue('--chart-rose-fill').trim() || FALLBACK_COLORS.roseFill,
	};
}

/**
 * Ordered palette for multi-series charts.
 * Returns [blue, rose, green, amber] border colors from the resolved set.
 */
export function chartPalette(colors: ChartColorSet): string[] {
	return [colors.blue, colors.rose, colors.green, colors.amber];
}

/**
 * Theme version counter — increments when the dark/light class changes on <html>.
 * Components can read this in `$effect` to reactively re-resolve chart colors
 * when the theme toggles at runtime.
 */
let _themeVersion = 0;
let _observers: Array<() => void> = [];

export function getThemeVersion(): number {
	return _themeVersion;
}

export function onThemeChange(callback: () => void): () => void {
	_observers.push(callback);
	return () => {
		_observers = _observers.filter((cb) => cb !== callback);
	};
}

// Start watching for theme class changes (client-only, runs once)
if (typeof document !== 'undefined') {
	const observer = new MutationObserver(() => {
		_themeVersion++;
		for (const cb of _observers) cb();
	});
	observer.observe(document.documentElement, {
		attributes: true,
		attributeFilter: ['class']
	});
}
