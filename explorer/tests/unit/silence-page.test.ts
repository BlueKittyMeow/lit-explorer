/**
 * Tests for Silence page — gap metrics, chart, longest silence callout.
 */

import { describe, it, expect, afterEach, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/svelte';
import SilencePage from '../../src/routes/[slug]/silence/+page.svelte';

// Mock Chart.js — canvas doesn't exist in jsdom
vi.mock('chart.js/auto', () => ({
	default: class MockChart {
		data = {};
		options = {};
		destroy() {}
		update() {}
		toBase64Image() { return 'data:image/png;base64,mock'; }
	}
}));

// Mock $app/state
vi.mock('$app/state', () => ({
	page: { params: { slug: 'test-analysis' } }
}));

afterEach(() => cleanup());

const manifest = {
	title: 'Test Manuscript', slug: 'test-analysis', source_file: 'test.txt',
	analyzed_at: new Date().toISOString(), engine_version: '0.1.0',
	word_count: 5000, char_count: 25000, chapter_count: 2,
	character_list: ['emil', 'felix'], analyzers_run: [], parameters: {}, warnings: []
};

const chapters = {
	chapters: [
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
	]
};

const silence = {
	gaps: [
		{ start_char: 0, end_char: 500, word_count: 80 },
		{ start_char: 800, end_char: 1200, word_count: 65 },
		{ start_char: 1500, end_char: 2800, word_count: 210 },
		{ start_char: 3000, end_char: 3400, word_count: 55 },
	],
	longest_silence: {
		word_count: 210,
		position: 0.3,
		preview: 'The room was quiet for a long time. Nobody spoke.'
	},
	avg_gap_words: 102.5,
	total_gaps: 4,
};

const data = { manifest, silence, chapters };

describe('Silence page', () => {
	it('renders total gaps metric', () => {
		render(SilencePage, { props: { data } });
		expect(screen.getByText('4')).toBeInTheDocument();
		expect(screen.getByText('Total Gaps')).toBeInTheDocument();
	});

	it('renders average gap word count', () => {
		render(SilencePage, { props: { data } });
		expect(screen.getByText('102.5')).toBeInTheDocument();
		expect(screen.getByText('Avg Gap Words')).toBeInTheDocument();
	});

	it('renders longest silence word count in metric card', () => {
		render(SilencePage, { props: { data } });
		expect(screen.getByText('210')).toBeInTheDocument();
		// "Longest Silence" appears in both MetricCard and callout
		expect(screen.getAllByText('Longest Silence')).toHaveLength(2);
	});

	it('renders longest silence preview text', () => {
		render(SilencePage, { props: { data } });
		expect(screen.getByText(/The room was quiet/)).toBeInTheDocument();
	});

	it('renders canvas for the chart', () => {
		render(SilencePage, { props: { data } });
		const canvas = document.querySelector('canvas');
		expect(canvas).not.toBeNull();
	});

	it('handles zero gaps gracefully', () => {
		const emptyData = {
			manifest,
			chapters,
			silence: {
				gaps: [],
				longest_silence: null,
				avg_gap_words: 0,
				total_gaps: 0,
			}
		};
		render(SilencePage, { props: { data: emptyData } });
		expect(screen.getByText('Total Gaps')).toBeInTheDocument();
		// total_gaps, avg_gap_words, and longest_silence all show 0
		expect(screen.getAllByText('0')).toHaveLength(3);
		// Should not show longest silence callout section when null
		expect(screen.queryByText(/The room was quiet/)).not.toBeInTheDocument();
	});
});
