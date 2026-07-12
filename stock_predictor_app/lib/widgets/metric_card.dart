// ============================================================
// widgets/metric_card.dart - Metric display card
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
    final accent = positive ? const Color(0xFF22C55E) : const Color(0xFFEF4444);

    return GlassCard(
      padding: const EdgeInsets.all(14),
      margin: EdgeInsets.zero,
      borderRadius: 8,
      child: IntrinsicHeight(
        child: ConstrainedBox(
          constraints: const BoxConstraints(minHeight: 116),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  if (icon != null) ...[
                    Icon(icon, size: 15, color: const Color(0xFF94A3B8)),
                    const SizedBox(width: 6),
                  ],
                  Expanded(
                    child: Text(
                      label.toUpperCase(),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: const Color(0xFF94A3B8).withValues(alpha: 0.92),
                        fontSize: 10.5,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0,
                        height: 1.2,
                      ),
                    ),
                  ),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  FittedBox(
                    alignment: Alignment.centerLeft,
                    fit: BoxFit.scaleDown,
                    child: Text(
                      value,
                      maxLines: 1,
                      style: const TextStyle(
                        color: Color(0xFFE2E8F0),
                        fontSize: 21,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                  if (delta != null) ...[
                    const SizedBox(height: 5),
                    Row(
                      children: [
                        Icon(
                          positive
                              ? Icons.arrow_upward_rounded
                              : Icons.arrow_downward_rounded,
                          color: accent,
                          size: 14,
                        ),
                        const SizedBox(width: 3),
                        Expanded(
                          child: Text(
                            delta!,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              color: accent,
                              fontSize: 12.5,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
