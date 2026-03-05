/** TypeScript interfaces matching the lit-engine JSON output contract. */

// manifest.json
export interface Manifest {
	title: string;
	slug: string;
	source_file: string;
	analyzed_at: string;
	engine_version: string;
	word_count: number;
	char_count: number;
	chapter_count: number;
	character_list: string[];
	analyzers_run: string[];
	parameters: Record<string, unknown>;
	warnings: string[];
}

// analysis.json — block metrics
export interface BlockMetrics {
	mattr: number;
	avg_sentence_length: number;
	max_sentence_length: number;
	flesch_ease: number;
	flesch_grade: number;
	gunning_fog: number;
	// Enriched by readability analyzer via CLI pipeline
	coleman_liau: number;
	smog: number;
	ari: number;
}

export interface Block {
	id: number;
	tile_index: number;
	start_char: number;
	end_char: number;
	word_count: number;
	sentence_count: number;
	metrics: BlockMetrics;
	sentence_lengths: number[];
	preview: string;
	chapter: number | null;
}

export interface Notable {
	longest_sentences: number[];
	highest_mattr: number[];
	highest_fog: number[];
	shortest_sentences: number[];
}

// Pacing data (merged into analysis.json by CLI when pacing analyzer runs)
export interface PacingPassage {
	block_id: number;
	avg_sentence_length: number;
	sentence_count: number;
	preview: string;
}

export interface PacingData {
	sentence_count: number;
	distribution: {
		mean: number;
		median: number;
		std_dev: number;
		min: number;
		max: number;
		percentiles: Record<string, number>;
	};
	staccato_passages: PacingPassage[];
	flowing_passages: PacingPassage[];
}

export interface Analysis {
	parameters: Record<string, number>;
	total_blocks: number;
	blocks: Block[];
	notable: Notable;
	pacing?: PacingData;
}

// characters.json
export interface VerbEntry {
	verb: string;
	count: number;
	category?: string;
}

export interface ActionEntry {
	action: string;
	count: number;
}

export interface PassiveAgent {
	agent: string;
	count: number;
}

export interface CharacterProfile {
	total_verbs: number;
	active_count: number;
	passive_count: number;
	intransitive_count: number;
	via_name: number;
	via_pronoun: number;
	verb_domains: Record<string, number>;
	top_verbs: VerbEntry[];
	top_actions: ActionEntry[];
	passive_verbs: VerbEntry[];
	passive_agents: PassiveAgent[];
}

export interface Characters {
	characters: Record<string, CharacterProfile>;
}

// chapters.json
export interface ChapterSentiment {
	compound: number;
	pos: number;
	neg: number;
	neu: number;
}

export interface Chapter {
	number: number;
	title: string;
	word_count: number;
	sentence_count: number;
	dialogue_ratio: number;
	avg_sentence_length: number;
	mattr: number;
	flesch_ease: number;
	fog: number;
	character_mentions: Record<string, number>;
	dominant_character: string;
	sentiment: ChapterSentiment;
	block_range: [number, number];
}

export interface Chapters {
	chapters: Chapter[];
}

// sentiment.json
export interface SentimentPoint {
	position: number;
	compound: number;
	pos: number;
	neg: number;
	neu: number;
}

export interface SmoothedPoint {
	position: number;
	compound: number;
}

export interface SentimentExtreme {
	position: number;
	text_preview: string;
	score: number;
}

export interface Sentiment {
	method: string;
	granularity: string;
	arc: SentimentPoint[];
	smoothed_arc: SmoothedPoint[];
	chapter_averages: { chapter: number; compound: number }[];
	extremes: {
		most_positive: SentimentExtreme | null;
		most_negative: SentimentExtreme | null;
	};
}

// Combined: everything loaded for a single analysis
export interface AnalysisData {
	manifest: Manifest;
	analysis: Analysis;
	characters: Characters;
	chapters: Chapters;
	sentiment: Sentiment;
}

// Landing page: summary for listing
export interface AnalysisSummary {
	slug: string;
	title: string;
	word_count: number;
	chapter_count: number;
	character_list: string[];
	analyzed_at: string;
	analyzers_run: string[];
}
