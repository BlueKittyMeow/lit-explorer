/**
 * Tests for Characters page — CharacterCard, VerbDomainChart, page rendering.
 */

import { describe, it, expect, afterEach, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/svelte';
import CharacterCard from '../../src/lib/components/CharacterCard.svelte';
import VerbDomainChart from '../../src/lib/components/VerbDomainChart.svelte';
import CharactersPage from '../../src/routes/[slug]/characters/+page.svelte';

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

const emilProfile = {
	total_verbs: 120, active_count: 115, passive_count: 5,
	intransitive_count: 60, via_name: 45, via_pronoun: 75,
	verb_domains: {
		perception: 20, cognition: 15, motion: 18,
		physical_action: 22, gesture: 10, emotion: 8, speech: 5, other: 22
	},
	top_verbs: [
		{ verb: 'see', count: 12, category: 'perception' },
		{ verb: 'walk', count: 8, category: 'motion' }
	],
	top_actions: [{ action: 'shake -> head', count: 3 }],
	passive_verbs: [{ verb: 'make', count: 2 }],
	passive_agents: [{ agent: 'darkness', count: 1 }]
};

const felixProfile = {
	total_verbs: 95, active_count: 90, passive_count: 5,
	intransitive_count: 45, via_name: 35, via_pronoun: 60,
	verb_domains: {
		perception: 12, cognition: 18, motion: 10,
		physical_action: 15, gesture: 8, emotion: 12, speech: 8, other: 12
	},
	top_verbs: [
		{ verb: 'think', count: 10, category: 'cognition' },
		{ verb: 'say', count: 6, category: 'speech' }
	],
	top_actions: [{ action: 'close -> eyes', count: 2 }],
	passive_verbs: [{ verb: 'tell', count: 2 }],
	passive_agents: []
};

const manifest = {
	title: 'Test Manuscript', slug: 'test-analysis', source_file: 'test.txt',
	analyzed_at: new Date().toISOString(), engine_version: '0.1.0',
	word_count: 5000, char_count: 25000, chapter_count: 2,
	character_list: ['emil', 'felix'], analyzers_run: [], parameters: {}, warnings: []
};

const data = {
	manifest,
	characters: { characters: { emil: emilProfile, felix: felixProfile } }
};

describe('CharacterCard', () => {
	it('renders character name', () => {
		render(CharacterCard, { props: { name: 'emil', profile: emilProfile } });
		expect(screen.getByText('emil')).toBeInTheDocument();
	});

	it('renders total verb count', () => {
		render(CharacterCard, { props: { name: 'emil', profile: emilProfile } });
		expect(screen.getByText('120')).toBeInTheDocument();
	});

	it('renders active/passive percentage', () => {
		render(CharacterCard, { props: { name: 'emil', profile: emilProfile } });
		// 115/120 = 95.8% active
		expect(screen.getByText(/96%/)).toBeInTheDocument();
	});

	it('renders top verbs', () => {
		render(CharacterCard, { props: { name: 'emil', profile: emilProfile } });
		expect(screen.getByText('see')).toBeInTheDocument();
		expect(screen.getByText('walk')).toBeInTheDocument();
	});

	it('renders top actions', () => {
		render(CharacterCard, { props: { name: 'emil', profile: emilProfile } });
		expect(screen.getByText('shake -> head')).toBeInTheDocument();
	});

	it('renders passive agents when present', () => {
		render(CharacterCard, { props: { name: 'emil', profile: emilProfile } });
		expect(screen.getByText('darkness')).toBeInTheDocument();
	});

	it('hides passive section when passive_count is 0', () => {
		const noPassiveProfile = { ...emilProfile, passive_count: 0, passive_verbs: [], passive_agents: [] };
		render(CharacterCard, { props: { name: 'test', profile: noPassiveProfile } });
		expect(screen.queryByText('Passive')).not.toBeInTheDocument();
	});

	it('renders via_name/via_pronoun ratio', () => {
		render(CharacterCard, { props: { name: 'emil', profile: emilProfile } });
		// via_name=45, via_pronoun=75, denominator = 45+75 = 120
		// namePercent = 45/120 = 37.5% → 38%
		expect(screen.getByText(/38%/)).toBeInTheDocument();
	});
});

describe('VerbDomainChart', () => {
	const chartData = {
		labels: ['perception', 'cognition', 'motion'],
		datasets: [{ label: 'Test', data: [20, 15, 18] }]
	};

	it('renders figure with accessible aria-label', () => {
		render(VerbDomainChart, { props: { data: chartData, label: 'Verb domains' } });
		const figure = screen.getByRole('img');
		expect(figure).toHaveAttribute('aria-label', 'Verb domains');
	});

	it('renders canvas element', () => {
		const { container } = render(VerbDomainChart, { props: { data: chartData } });
		expect(container.querySelector('canvas')).toBeInTheDocument();
	});
});

describe('Characters page', () => {
	it('renders both character cards', () => {
		render(CharactersPage, { props: { data } });
		expect(screen.getByText('emil')).toBeInTheDocument();
		expect(screen.getByText('felix')).toBeInTheDocument();
	});
});
