/**
 * Tests for Chapters page — sortable table, summary stats, sentiment indicators.
 */

import { describe, it, expect, afterEach, vi } from 'vitest';
import { render, screen, cleanup, fireEvent } from '@testing-library/svelte';
import ChaptersPage from '../../src/routes/[slug]/chapters/+page.svelte';

// Mock Chart.js — canvas doesn't exist in jsdom
vi.mock('chart.js/auto', () => ({
	default: class MockChart {
		destroy() {}
	}
}));

// Mock $app/state
vi.mock('$app/state', () => ({
	page: { params: { slug: 'test-analysis' } }
}));

afterEach(() => cleanup());

const chapters = [
	{
		number: 1, title: 'Café Union', word_count: 3100, sentence_count: 180,
		dialogue_ratio: 0.42, avg_sentence_length: 17.2, mattr: 0.795,
		flesch_ease: 68.0, fog: 10.5,
		character_mentions: { emil: 28, felix: 30 }, dominant_character: 'shared',
		sentiment: { compound: 0.12, pos: 0.08, neg: 0.04, neu: 0.88 },
		block_range: [1, 3] as [number, number]
	},
	{
		number: 2, title: 'The Theatre', word_count: 1900, sentence_count: 110,
		dialogue_ratio: 0.35, avg_sentence_length: 17.3, mattr: 0.810,
		flesch_ease: 73.5, fog: 9.0,
		character_mentions: { emil: 5, felix: 2 }, dominant_character: 'emil',
		sentiment: { compound: -0.05, pos: 0.04, neg: 0.06, neu: 0.90 },
		block_range: [4, 5] as [number, number]
	}
];

const manifest = {
	title: 'Test Manuscript', slug: 'test-analysis', source_file: 'test.txt',
	analyzed_at: new Date().toISOString(), engine_version: '0.1.0',
	word_count: 5000, char_count: 25000, chapter_count: 2,
	character_list: ['emil', 'felix'], analyzers_run: [], parameters: {}, warnings: []
};

const data = { manifest, chapters: { chapters } };

describe('Chapters page', () => {
	it('renders chapter titles', () => {
		render(ChaptersPage, { props: { data } });
		expect(screen.getByText('Café Union')).toBeInTheDocument();
		expect(screen.getByText('The Theatre')).toBeInTheDocument();
	});

	it('renders word counts', () => {
		render(ChaptersPage, { props: { data } });
		expect(screen.getByText('3,100')).toBeInTheDocument();
		expect(screen.getByText('1,900')).toBeInTheDocument();
	});

	it('renders dialogue ratios as percentages', () => {
		render(ChaptersPage, { props: { data } });
		expect(screen.getByText('42%')).toBeInTheDocument();
		expect(screen.getByText('35%')).toBeInTheDocument();
	});

	it('renders summary stats via MetricCards', () => {
		render(ChaptersPage, { props: { data } });
		expect(screen.getByText('Chapters')).toBeInTheDocument();
		expect(screen.getByText('2,500')).toBeInTheDocument(); // avg words (5000/2)
		expect(screen.getByText('39%')).toBeInTheDocument(); // avg dialogue
	});

	it('renders sentiment indicators', () => {
		const { container } = render(ChaptersPage, { props: { data } });
		const dots = container.querySelectorAll('.sentiment-dot');
		expect(dots.length).toBe(2);
	});

	it('renders dominant character chips', () => {
		render(ChaptersPage, { props: { data } });
		expect(screen.getByText('shared')).toBeInTheDocument();
		expect(screen.getByText('emil')).toBeInTheDocument();
	});

	it('sort toggle changes order and updates aria-sort', async () => {
		render(ChaptersPage, { props: { data } });
		// Find the "Words" column header button
		const wordsHeader = screen.getByRole('button', { name: /words/i });
		expect(wordsHeader).toBeInTheDocument();

		// Click to sort by words (ascending first click)
		await fireEvent.click(wordsHeader);

		// Get all table rows (excluding header)
		const rows = screen.getAllByRole('row');
		// First data row should be The Theatre (1900) after ascending sort
		const firstDataRow = rows[1]; // rows[0] is header
		expect(firstDataRow.textContent).toContain('The Theatre');

		// Verify aria-sort attribute on the column header
		const th = wordsHeader.closest('th');
		expect(th).toHaveAttribute('aria-sort');
	});

	it('renders table with sticky first column class', () => {
		const { container } = render(ChaptersPage, { props: { data } });
		const wrapper = container.querySelector('.table-wrapper');
		expect(wrapper).toBeInTheDocument();
	});

	it('chapter number links to blocks page', () => {
		render(ChaptersPage, { props: { data } });
		const link = screen.getByRole('link', { name: '1' });
		expect(link).toHaveAttribute('href', '/test-analysis/blocks?from=1');
	});

	it('aria-sort transitions between ascending and descending', async () => {
		render(ChaptersPage, { props: { data } });
		const wordsHeader = screen.getByRole('button', { name: /words/i });
		const th = wordsHeader.closest('th')!;

		// Initially none (default sort is by number, not words)
		expect(th).toHaveAttribute('aria-sort', 'none');

		// Click to sort ascending
		await fireEvent.click(wordsHeader);
		expect(th).toHaveAttribute('aria-sort', 'ascending');

		// Click again to sort descending
		await fireEvent.click(wordsHeader);
		expect(th).toHaveAttribute('aria-sort', 'descending');
	});

	it('previous column loses aria-sort when different column is sorted', async () => {
		render(ChaptersPage, { props: { data } });
		const wordsHeader = screen.getByRole('button', { name: /words/i });
		const fogHeader = screen.getByRole('button', { name: /fog/i });

		// Sort by words first
		await fireEvent.click(wordsHeader);
		expect(wordsHeader.closest('th')).toHaveAttribute('aria-sort', 'ascending');

		// Sort by fog — words should revert to none
		await fireEvent.click(fogHeader);
		expect(wordsHeader.closest('th')).toHaveAttribute('aria-sort', 'none');
		expect(fogHeader.closest('th')).toHaveAttribute('aria-sort', 'ascending');
	});

	it('default sort has chapter number ascending', () => {
		const { container } = render(ChaptersPage, { props: { data } });
		// The # column header should have aria-sort="ascending" by default
		const headers = container.querySelectorAll('th');
		const numberHeader = headers[0]; // First column is #
		expect(numberHeader).toHaveAttribute('aria-sort', 'ascending');
	});
});
