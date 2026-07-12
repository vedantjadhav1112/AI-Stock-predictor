// ============================================================
// widgets/metric_card.dart — Metric Display Card
// ============================================================
import 'package:flutter/material.dart';
import 'glass_card.dart';

class MetricCard extends StatelessWidget {
  final String label;
  final String value;
  final String? delta;
  final bool positive;
  final IconData? icon;

  const MetricCard({
    super.key,
    required this.label,
    required this.value,
    this.delta,
    this.positive = true,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              if (icon != null) ...[
                Icon(icon, size: 14, color: const Color(0xFF94A3B8)),
                const SizedBox(width: 6),
              ],
              Expanded(
                child: Text(
                  label.toUpperCase(),
                  style: TextStyle(
                    color: const Color(0xFF94A3B8).withValues(alpha: 0.9),
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 0.5,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: const TextStyle(
              color: Color(0xFFE2E8F0),
              fontSize: 20,
              fontWeight: FontWeight.w700,
            ),
          ),
          if (delta != null) ...[
            const SizedBox(height: 4),
            Text(
              delta!,
              style: TextStyle(
                color: positive
                    ? const Color(0xFF22C55E)
                    : const Color(0xFFEF4444),
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
