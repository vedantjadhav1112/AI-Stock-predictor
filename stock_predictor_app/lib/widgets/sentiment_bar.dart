// ============================================================
// widgets/sentiment_bar.dart — Sentiment Breakdown Widget
// ============================================================
import 'package:flutter/material.dart';
import '../models/stock_analysis.dart';

class SentimentBar extends StatelessWidget {
  final SentimentResult sentiment;

  const SentimentBar({super.key, required this.sentiment});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Overall sentiment badge
        Row(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: _sentimentGradient(sentiment.overallSentiment),
                ),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                '${_sentimentIcon(sentiment.overallSentiment)} ${sentiment.overallSentiment}',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                  fontSize: 14,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Text(
              'Confidence: ${(sentiment.confidence * 100).toStringAsFixed(0)}%',
              style: TextStyle(
                color: const Color(0xFF94A3B8).withValues(alpha: 0.8),
                fontSize: 13,
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),

        // Breakdown bars
        _breakdownRow('Bullish', sentiment.positivePct, const Color(0xFF22C55E)),
        const SizedBox(height: 10),
        _breakdownRow('Bearish', sentiment.negativePct, const Color(0xFFEF4444)),
        const SizedBox(height: 10),
        _breakdownRow('Neutral', sentiment.neutralPct, const Color(0xFF94A3B8)),
      ],
    );
  }

  Widget _breakdownRow(String label, double pct, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: TextStyle(
                color: color.withValues(alpha: 0.9),
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
            Text(
              '${pct.toStringAsFixed(0)}%',
              style: TextStyle(
                color: color.withValues(alpha: 0.9),
                fontSize: 13,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: pct / 100,
            backgroundColor: color.withValues(alpha: 0.1),
            valueColor: AlwaysStoppedAnimation<Color>(color),
            minHeight: 6,
          ),
        ),
      ],
    );
  }

  String _sentimentIcon(String sentiment) {
    switch (sentiment) {
      case 'Bullish':
        return '🟢';
      case 'Bearish':
        return '🔴';
      default:
        return '⚪';
    }
  }

  List<Color> _sentimentGradient(String sentiment) {
    switch (sentiment) {
      case 'Bullish':
        return [const Color(0xFF16A34A), const Color(0xFF22C55E)];
      case 'Bearish':
        return [const Color(0xFFDC2626), const Color(0xFFEF4444)];
      default:
        return [const Color(0xFF64748B), const Color(0xFF94A3B8)];
    }
  }
}
