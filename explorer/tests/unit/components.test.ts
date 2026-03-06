/**
 * Component smoke tests for shared UI components.
 *
 * Uses @testing-library/svelte to render components in jsdom.
 * MiniChart chart rendering is not tested (Chart.js needs real canvas),
 * but the accessibility wrapper (figure/figcaption) is verified.
 */

import { describe, it, expect, afterEach, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/svelte';
import MetricCard from '../../src/lib/components/MetricCard.svelte';
import MiniChart from '../../src/lib/components/MiniChart.svelte';
import AnalysisCard from '../../src/lib/components/AnalysisCard.svelte';

// Mock Chart.js — canvas doesn't exist in jsdom
vi.mock('chart.js/auto', () => ({
	default: class MockChart {
		destroy() {}
	}
}));

afterEach(() => cleanup());

describe('MetricCard', () => {
	it('renders label and value', () => {
		render(MetricCard, { props: { label: 'Words', value: '12,345' } });
		expect(screen.getByText('Words')).toBeInTheDocument();
		expect(screen.getByText('12,345')).toBeInTheDocument();
	});

	it('renders numeric value', () => {
		render(MetricCard, { props: { label: 'Blocks', value: 42 } });
		expect(screen.getByText('42')).toBeInTheDocument();
	});

	it('renders subtitle when provided', () => {
		render(MetricCard, { props: { label: 'Flesch', value: '65.2', subtitle: 'ease score' } });
		expect(screen.getByText('ease score')).toBeInTheDocument();
	});

	it('does not render subtitle when absent', () => {
		render(MetricCard, { props: { label: 'Words', value: 100 } });
		expect(screen.queryByText('ease score')).not.toBeInTheDocument();
	});
});

describe('MiniChart', () => {
	const chartData = {
		labels: [1, 2, 3],
		datasets: [{ label: 'Test', data: [0.5, 0.8, 0.3] }]
	};

	it('renders figure with aria-label', () => {
		render(MiniChart, { props: { data: chartData, label: 'Sentiment arc' } });
		const figure = screen.getByRole('img');
		expect(figure).toHaveAttribute('aria-label', 'Sentiment arc');
	});

	it('renders sr-only figcaption with data point count', () => {
		render(MiniChart, { props: { data: chartData, label: 'Test chart' } });
		expect(screen.getByText('Test chart: 3 data points')).toBeInTheDocument();
	});

	it('renders canvas element', () => {
		const { container } = render(MiniChart, { props: { data: chartData } });
		expect(container.querySelector('canvas')).toBeInTheDocument();
	});
});

describe('AnalysisCard', () => {
	const analysis = {
		slug: 'test-novel',
		title: 'The Test Novel',
		word_count: 50000,
		chapter_count: 16,
		character_list: ['emil', 'felix', 'clara'],
		analyzed_at: new Date().toISOString(),
		analyzers_run: ['texttiling', 'agency', 'sentiment']
	};

	it('renders title', () => {
		render(AnalysisCard, { props: { analysis } });
		expect(screen.getByText('The Test Novel')).toBeInTheDocument();
	});

	it('renders word count', () => {
		render(AnalysisCard, { props: { analysis } });
		expect(screen.getByText('50,000 words')).toBeInTheDocument();
	});

	it('renders chapter count', () => {
		render(AnalysisCard, { props: { analysis } });
		expect(screen.getByText('16 chapters')).toBeInTheDocument();
	});

	it('renders analyzer count', () => {
		render(AnalysisCard, { props: { analysis } });
		expect(screen.getByText('3 analyzers')).toBeInTheDocument();
	});

	it('renders character chips', () => {
		render(AnalysisCard, { props: { analysis } });
		expect(screen.getByText('emil')).toBeInTheDocument();
		expect(screen.getByText('felix')).toBeInTheDocument();
		expect(screen.getByText('clara')).toBeInTheDocument();
	});

	it('links to overview page', () => {
		render(AnalysisCard, { props: { analysis } });
		const link = screen.getByRole('link');
		expect(link).toHaveAttribute('href', '/test-novel/overview');
	});

	it('shows relative time', () => {
		render(AnalysisCard, { props: { analysis } });
		// analyzed_at is now, so should show "just now"
		expect(screen.getByText('just now')).toBeInTheDocument();
	});
});
