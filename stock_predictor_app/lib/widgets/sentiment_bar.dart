// ============================================================
// widgets/sentiment_bar.dart - Sentiment breakdown widget
// ============================================================
import 'package:flutter/material.dart';
import '../models/stock_analysis.dart';

class SentimentBar extends StatelessWidget {
  final SentimentResult sentiment;

  const SentimentBar({super.key, required this.sentiment});

  @override
  Widget build(BuildContext context) {
    final sentimentColor = _sentimentColor(sentiment.overallSentiment);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          spacing: 12,
          runSpacing: 10,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              decoration: BoxDecoration(
                color: sentimentColor.withValues(alpha: 0.18),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: sentimentColor.withValues(alpha: 0.34),
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: sentimentColor,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    sentiment.overallSentiment,
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w800,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
            Text(
              'Confidence ${(sentiment.confidence * 100).toStringAsFixed(0)}%',
              style: TextStyle(
                color: const Color(0xFF94A3B8).withValues(alpha: 0.88),
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),
        _breakdownRow(
          'Bullish',
          sentiment.positivePct,
          const Color(0xFF22C55E),
        ),
        const SizedBox(height: 10),
        _breakdownRow(
          'Bearish',
          sentiment.negativePct,
          const Color(0xFFEF4444),
        ),
        const SizedBox(height: 10),
        _breakdownRow('Neutral', sentiment.neutralPct, const Color(0xFF94A3B8)),
      ],
    );
  }

  Widget _breakdownRow(String label, double pct, Color color) {
    final value = (pct / 100).clamp(0.0, 1.0);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: TextStyle(
                color: color.withValues(alpha: 0.94),
                fontSize: 13,
                fontWeight: FontWeight.w700,
              ),
            ),
            Text(
              '${pct.toStringAsFixed(0)}%',
              style: TextStyle(
                color: color.withValues(alpha: 0.94),
                fontSize: 13,
                fontWeight: FontWeight.w800,
              ),
            ),
          ],
        ),
        const SizedBox(height: 5),
        ClipRRect(
          borderRadius: BorderRadius.circular(5),
          child: LinearProgressIndicator(
            value: value,
            backgroundColor: color.withValues(alpha: 0.12),
            valueColor: AlwaysStoppedAnimation<Color>(color),
            minHeight: 7,
          ),
        ),
      ],
    );
  }

  Color _sentimentColor(String sentiment) {
    switch (sentiment) {
      case 'Bullish':
        return const Color(0xFF22C55E);
      case 'Bearish':
        return const Color(0xFFEF4444);
      default:
        return const Color(0xFF94A3B8);
    }
  }
}
