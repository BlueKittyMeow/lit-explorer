/**
 * Tests for PNG chart export utility.
 */

import { describe, it, expect, vi } from 'vitest';
import { exportChartAsPng } from '../../src/lib/utils/chart-export';

describe('exportChartAsPng', () => {
	it('does nothing when chart is undefined', () => {
		// Should not throw
		expect(() => exportChartAsPng(undefined, 'test.png')).not.toThrow();
	});

	it('calls toBase64Image and triggers download', () => {
		const mockChart = {
			toBase64Image: vi.fn().mockReturnValue('data:image/png;base64,abc')
		};
		const mockLink = { href: '', download: '', click: vi.fn() };
		vi.spyOn(document, 'createElement').mockReturnValueOnce(mockLink as any);

		exportChartAsPng(mockChart, 'test-chart.png');

		expect(mockChart.toBase64Image).toHaveBeenCalledWith('image/png', 1.0);
		expect(mockLink.download).toBe('test-chart.png');
		expect(mockLink.click).toHaveBeenCalled();
	});

	it('uses default filename when none provided', () => {
		const mockChart = {
			toBase64Image: vi.fn().mockReturnValue('data:image/png;base64,abc')
		};
		const mockLink = { href: '', download: '', click: vi.fn() };
		vi.spyOn(document, 'createElement').mockReturnValueOnce(mockLink as any);

		exportChartAsPng(mockChart);

		expect(mockLink.download).toBe('chart.png');
	});
});
