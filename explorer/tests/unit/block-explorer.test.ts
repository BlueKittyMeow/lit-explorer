/**
 * Tests for Block Explorer page — BlockReader, BlockMetricsPanel, interactive chart.
 */

import { describe, it, expect, afterEach, vi } from 'vitest';
import { render, screen, cleanup, fireEvent } from '@testing-library/svelte';
import BlockReader from '../../src/lib/components/BlockReader.svelte';
import BlockMetricsPanel from '../../src/lib/components/BlockMetricsPanel.svelte';
import BlocksPage from '../../src/routes/[slug]/blocks/+page.svelte';

// Mock Chart.js — canvas doesn't exist in jsdom
vi.mock('chart.js/auto', () => ({
	default: class MockChart {
		data = {};
		options = {};
		destroy() {}
		update() {}
	}
}));

// Mock $app/state
vi.mock('$app/state', () => ({
	page: { params: { slug: 'test-analysis' }, url: { searchParams: new URLSearchParams() } }
}));

afterEach(() => cleanup());

const block1 = {
	id: 1, tile_index: 0, start_char: 0, end_char: 1000,
	word_count: 160, sentence_count: 8,
	metrics: {
		mattr: 0.812, avg_sentence_length: 20.0, max_sentence_length: 45,
		flesch_ease: 65.2, flesch_grade: 9.1, gunning_fog: 11.3,
		coleman_liau: 10.2, smog: 9.8, ari: 10.5
	},
	sentence_lengths: [20, 15, 45, 12, 18, 22, 30, 8],
	preview: 'When lights were paling one by one...',
	longest_sentence_preview: 'The chandelier hung from the vaulted ceiling casting long amber shadows...',
	chapter: 1
};

const block2 = {
	id: 2, tile_index: 1, start_char: 1000, end_char: 2100,
	word_count: 180, sentence_count: 10,
	metrics: {
		mattr: 0.795, avg_sentence_length: 18.0, max_sentence_length: 38,
		flesch_ease: 70.1, flesch_grade: 8.2, gunning_fog: 9.8,
		coleman_liau: 9.1, smog: 8.5, ari: 9.0
	},
	sentence_lengths: [18, 22, 14, 20, 38, 10, 16, 24, 12, 6],
	preview: 'Emil walked to the window and paused...',
	longest_sentence_preview: 'He looked out across the rooftops remembering the conversation...',
	chapter: 1
};

const notable = {
	longest_sentences: [1, 3],
	highest_mattr: [4, 1],
	highest_fog: [1, 3],
	shortest_sentences: [5]
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

const manifest = {
	title: 'Test Manuscript', slug: 'test-analysis', source_file: 'test.txt',
	analyzed_at: new Date().toISOString(), engine_version: '0.1.0',
	word_count: 5000, char_count: 25000, chapter_count: 2,
	character_list: ['emil', 'felix'], analyzers_run: [], parameters: {}, warnings: []
};

const analysis = {
	parameters: { w: 40, k: 20, mattr_window: 50 },
	total_blocks: 2,
	blocks: [block1, block2],
	notable
};

const data = { manifest, analysis, chapters };

describe('BlockReader', () => {
	it('renders preview text', () => {
		render(BlockReader, { props: { block: block1, chapterTitle: 'Café Union' } });
		expect(screen.getByText(/When lights were paling/)).toBeInTheDocument();
	});

	it('renders block ID', () => {
		render(BlockReader, { props: { block: block1 } });
		expect(screen.getByText(/Block 1/)).toBeInTheDocument();
	});

	it('renders chapter chip when provided', () => {
		render(BlockReader, { props: { block: block1, chapterTitle: 'Café Union' } });
		expect(screen.getByText('Café Union')).toBeInTheDocument();
	});

	it('renders longest_sentence_preview when different from preview', () => {
		render(BlockReader, { props: { block: block1 } });
		expect(screen.getByText(/The chandelier hung/)).toBeInTheDocument();
	});
});

describe('BlockMetricsPanel', () => {
	it('renders metric values', () => {
		render(BlockMetricsPanel, { props: { block: block1 } });
		expect(screen.getByText('0.812')).toBeInTheDocument(); // MATTR
		expect(screen.getByText('65.2')).toBeInTheDocument(); // Flesch
		expect(screen.getByText('11.3')).toBeInTheDocument(); // Fog
	});

	it('renders notable badges when block is notable', () => {
		render(BlockMetricsPanel, { props: { block: block1, notable } });
		expect(screen.getByText('Longest sentences')).toBeInTheDocument();
		expect(screen.getByText('Highest Fog')).toBeInTheDocument();
	});
});

describe('Blocks page', () => {
	it('renders canvas for main chart', () => {
		const { container } = render(BlocksPage, { props: { data } });
		expect(container.querySelector('canvas')).toBeInTheDocument();
	});

	it('renders metric selector tabs', () => {
		render(BlocksPage, { props: { data } });
		expect(screen.getByRole('button', { name: /mattr/i })).toBeInTheDocument();
		expect(screen.getByRole('button', { name: /fog/i })).toBeInTheDocument();
	});

	it('renders prev/next navigation buttons', () => {
		render(BlocksPage, { props: { data } });
		expect(screen.getByRole('button', { name: /prev/i })).toBeInTheDocument();
		expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
	});

	it('has aria-live region for selection announcements', () => {
		const { container } = render(BlocksPage, { props: { data } });
		const liveRegion = container.querySelector('[aria-live]');
		expect(liveRegion).toBeInTheDocument();
	});
});
