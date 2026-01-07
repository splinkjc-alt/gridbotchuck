"""
Sentiment Analysis for Financial News
=====================================
Uses VADER (Valence Aware Dictionary and sEntiment Reasoner) with
financial term enhancements for stock news analysis.
"""

import re
from dataclasses import dataclass


@dataclass
class SentimentResult:
    """Sentiment analysis result."""
    score: float  # -1 (bearish) to +1 (bullish)
    confidence: float  # 0-1 confidence level
    label: str  # "bullish", "bearish", "neutral"
    keywords: list  # Key terms found


class SentimentAnalyzer:
    """
    Financial news sentiment analyzer.

    Uses a custom dictionary optimized for stock market news.
    """

    def __init__(self):
        # Bullish terms and their weights
        self.bullish_terms = {
            # Strong bullish
            'surge': 0.8, 'soar': 0.8, 'skyrocket': 0.9, 'breakthrough': 0.7,
            'beat': 0.6, 'beats': 0.6, 'exceeded': 0.6, 'exceeds': 0.6,
            'upgrade': 0.7, 'upgraded': 0.7, 'buy rating': 0.8,
            'outperform': 0.6, 'bullish': 0.7, 'rally': 0.6, 'rallies': 0.6,
            'record high': 0.7, 'all-time high': 0.8, 'ath': 0.7,
            'profit': 0.4, 'profits': 0.4, 'profitable': 0.5,
            'growth': 0.4, 'growing': 0.4, 'grew': 0.4,
            'strong': 0.3, 'strength': 0.3, 'positive': 0.4,
            'gain': 0.4, 'gains': 0.4, 'up': 0.2, 'rise': 0.3, 'rises': 0.3,
            'boost': 0.4, 'boosted': 0.4, 'jumps': 0.5, 'jump': 0.5,
            'recovery': 0.4, 'recover': 0.4, 'rebounds': 0.5,
            'momentum': 0.3, 'optimism': 0.4, 'optimistic': 0.4,
            'winner': 0.5, 'win': 0.3, 'success': 0.4,
            'expansion': 0.4, 'expand': 0.3, 'deal': 0.3,
            'partnership': 0.3, 'acquisition': 0.3, 'launch': 0.3,
            'dividend': 0.3, 'buyback': 0.4,

            # Moderate bullish
            'steady': 0.2, 'stable': 0.2, 'solid': 0.3,
            'improve': 0.3, 'improved': 0.3, 'improving': 0.3,
            'opportunity': 0.3, 'potential': 0.2,
        }

        # Bearish terms and their weights (negative values)
        self.bearish_terms = {
            # Strong bearish
            'crash': -0.9, 'plunge': -0.8, 'plummet': -0.8, 'collapse': -0.8,
            'bankruptcy': -0.9, 'bankrupt': -0.9, 'default': -0.7,
            'fraud': -0.9, 'scandal': -0.8, 'investigation': -0.6,
            'lawsuit': -0.5, 'sued': -0.5, 'fine': -0.4, 'penalty': -0.5,
            'downgrade': -0.7, 'downgraded': -0.7, 'sell rating': -0.8,
            'miss': -0.5, 'misses': -0.5, 'missed': -0.5,
            'loss': -0.5, 'losses': -0.5, 'losing': -0.4,
            'decline': -0.4, 'declines': -0.4, 'declining': -0.4,
            'fall': -0.3, 'falls': -0.3, 'fell': -0.4, 'fallen': -0.4,
            'drop': -0.4, 'drops': -0.4, 'dropped': -0.4,
            'bearish': -0.7, 'selloff': -0.6, 'sell-off': -0.6,
            'weak': -0.4, 'weakness': -0.4, 'negative': -0.4,
            'warning': -0.5, 'warns': -0.5, 'concern': -0.4, 'concerns': -0.4,
            'risk': -0.3, 'risks': -0.3, 'risky': -0.4,
            'cut': -0.3, 'cuts': -0.3, 'layoff': -0.5, 'layoffs': -0.5,
            'recession': -0.6, 'slowdown': -0.4, 'slowing': -0.3,
            'inflation': -0.3, 'rate hike': -0.4,
            'delay': -0.3, 'delayed': -0.3, 'postpone': -0.3,
            'struggle': -0.4, 'struggles': -0.4, 'struggling': -0.4,
            'disappointing': -0.5, 'disappointed': -0.4,
            'underperform': -0.5, 'underperforms': -0.5,

            # Moderate bearish
            'uncertain': -0.3, 'uncertainty': -0.3,
            'volatile': -0.2, 'volatility': -0.2,
            'pressure': -0.2, 'headwind': -0.3, 'headwinds': -0.3,
        }

        # Intensity modifiers
        self.intensifiers = {
            'very': 1.3, 'extremely': 1.5, 'significantly': 1.3,
            'sharply': 1.4, 'dramatically': 1.4, 'substantially': 1.3,
            'slightly': 0.7, 'marginally': 0.6, 'somewhat': 0.8,
            'huge': 1.4, 'massive': 1.4, 'major': 1.2,
        }

        # Negation words
        self.negations = {'not', 'no', 'never', 'neither', 'nobody', 'nothing',
                         "n't", 'dont', "don't", 'doesnt', "doesn't",
                         'didnt', "didn't", 'wont', "won't", 'cant', "can't"}

    def analyze(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of news text.

        Args:
            text: News headline or article text

        Returns:
            SentimentResult with score, confidence, label, and keywords
        """
        if not text:
            return SentimentResult(0, 0, "neutral", [])

        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)

        total_score = 0
        term_count = 0
        keywords = []

        # Check for multi-word phrases first
        all_terms = {**self.bullish_terms, **self.bearish_terms}
        for phrase, weight in sorted(all_terms.items(), key=lambda x: -len(x[0])):
            if ' ' in phrase and phrase in text_lower:
                total_score += weight
                term_count += 1
                keywords.append((phrase, weight))

        # Check individual words with context
        for i, word in enumerate(words):
            weight = 0

            if word in self.bullish_terms:
                weight = self.bullish_terms[word]
            elif word in self.bearish_terms:
                weight = self.bearish_terms[word]

            if weight != 0:
                # Check for negation in previous 3 words
                negated = False
                for j in range(max(0, i-3), i):
                    if words[j] in self.negations:
                        negated = True
                        break

                if negated:
                    weight *= -0.5  # Flip and reduce

                # Check for intensifiers
                for j in range(max(0, i-2), i):
                    if words[j] in self.intensifiers:
                        weight *= self.intensifiers[words[j]]
                        break

                total_score += weight
                term_count += 1
                keywords.append((word, weight))

        # Calculate final score (-1 to 1)
        if term_count > 0:
            avg_score = total_score / term_count
            # Also factor in total magnitude
            magnitude_bonus = min(0.3, term_count * 0.05)
            if total_score > 0:
                final_score = min(1.0, avg_score + magnitude_bonus)
            else:
                final_score = max(-1.0, avg_score - magnitude_bonus)
        else:
            final_score = 0

        # Determine label
        if final_score > 0.15:
            label = "bullish"
        elif final_score < -0.15:
            label = "bearish"
        else:
            label = "neutral"

        # Confidence based on term count and score magnitude
        confidence = min(1.0, (term_count * 0.15) + (abs(final_score) * 0.5))

        return SentimentResult(
            score=round(final_score, 3),
            confidence=round(confidence, 3),
            label=label,
            keywords=keywords[:10]  # Top 10 keywords
        )

    def analyze_multiple(self, texts: list[str]) -> SentimentResult:
        """Analyze multiple headlines and return aggregate sentiment."""
        if not texts:
            return SentimentResult(0, 0, "neutral", [])

        results = [self.analyze(t) for t in texts]

        # Weighted average by confidence
        total_weight = sum(r.confidence for r in results)
        if total_weight == 0:
            return SentimentResult(0, 0, "neutral", [])

        weighted_score = sum(r.score * r.confidence for r in results) / total_weight
        avg_confidence = sum(r.confidence for r in results) / len(results)

        # Collect all keywords
        all_keywords = []
        for r in results:
            all_keywords.extend(r.keywords)

        if weighted_score > 0.15:
            label = "bullish"
        elif weighted_score < -0.15:
            label = "bearish"
        else:
            label = "neutral"

        return SentimentResult(
            score=round(weighted_score, 3),
            confidence=round(avg_confidence, 3),
            label=label,
            keywords=all_keywords[:15]
        )
