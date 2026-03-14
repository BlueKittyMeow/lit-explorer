/**
 * Export a Chart.js instance as a PNG file.
 * Uses the chart's built-in toBase64Image() method.
 */
export function exportChartAsPng(
	chart: { toBase64Image: (type?: string, quality?: number) => string } | undefined,
	filename: string = 'chart.png'
): void {
	if (!chart || typeof document === 'undefined') return;

	const dataUrl = chart.toBase64Image('image/png', 1.0);
	const link = document.createElement('a');
	link.href = dataUrl;
	link.download = filename;
	link.click();
}
