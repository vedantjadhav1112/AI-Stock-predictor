// ============================================================
// widgets/stock_chart.dart - Price line chart
// ============================================================
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import '../models/stock_analysis.dart';

class StockChart extends StatelessWidget {
  final List<ChartDataPoint> data;
  final String ticker;

  const StockChart({super.key, required this.data, required this.ticker});

  @override
  Widget build(BuildContext context) {
    if (data.isEmpty) {
      return const SizedBox(
        height: 220,
        child: Center(
          child: Text(
            'No chart data available',
            style: TextStyle(color: Color(0xFF94A3B8)),
          ),
        ),
      );
    }

    final closePrices = data.map((e) => e.close).toList();
    final sma20Prices = data.map((e) => e.sma20).toList();
    final allPrices = [
      ...closePrices,
      ...sma20Prices.where((price) => price > 0),
    ];
    final minPrice = allPrices.reduce((a, b) => a < b ? a : b);
    final maxPrice = allPrices.reduce((a, b) => a > b ? a : b);
    final padding = (maxPrice - minPrice).abs() < 0.01
        ? maxPrice * 0.03
        : (maxPrice - minPrice) * 0.08;
    final minY = (minPrice - padding).clamp(0.0, double.infinity);
    final maxY = maxPrice + padding;
    final horizontalInterval = ((maxY - minY) / 4).clamp(0.01, double.infinity);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                '${ticker.toUpperCase()} Price History',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: Color(0xFFE2E8F0),
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
            const SizedBox(width: 8),
            _legend(const Color(0xFF3B82F6), 'Close'),
          ],
        ),
        const SizedBox(height: 16),
        SizedBox(
          height: 260,
          child: LineChart(
            LineChartData(
              minY: minY,
              maxY: maxY,
              gridData: FlGridData(
                show: true,
                drawVerticalLine: false,
                horizontalInterval: horizontalInterval,
                getDrawingHorizontalLine: (value) => FlLine(
                  color: const Color(0xFF63B3ED).withValues(alpha: 0.08),
                  strokeWidth: 1,
                ),
              ),
              titlesData: FlTitlesData(
                topTitles: const AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
                rightTitles: const AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    reservedSize: 28,
                    interval: (data.length / 4).ceilToDouble(),
                    getTitlesWidget: (value, meta) {
                      final idx = value.toInt();
                      if (idx < 0 || idx >= data.length) {
                        return const SizedBox.shrink();
                      }
                      final parts = data[idx].date.split('-');
                      final label = parts.length == 3
                          ? '${parts[1]}/${parts[2]}'
                          : data[idx].date;
                      return Padding(
                        padding: const EdgeInsets.only(top: 8),
                        child: Text(
                          label,
                          style: TextStyle(
                            color: const Color(
                              0xFF94A3B8,
                            ).withValues(alpha: 0.72),
                            fontSize: 10,
                          ),
                        ),
                      );
                    },
                  ),
                ),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    reservedSize: 48,
                    interval: horizontalInterval,
                    getTitlesWidget: (value, meta) {
                      return Text(
                        '\$${value.toStringAsFixed(0)}',
                        style: TextStyle(
                          color: const Color(
                            0xFF94A3B8,
                          ).withValues(alpha: 0.72),
                          fontSize: 10,
                        ),
                      );
                    },
                  ),
                ),
              ),
              borderData: FlBorderData(show: false),
              lineBarsData: [
                LineChartBarData(
                  spots: List.generate(
                    closePrices.length,
                    (i) => FlSpot(i.toDouble(), closePrices[i]),
                  ),
                  isCurved: true,
                  color: const Color(0xFF3B82F6),
                  barWidth: 2.6,
                  dotData: const FlDotData(show: false),
                  belowBarData: BarAreaData(
                    show: true,
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [
                        const Color(0xFF3B82F6).withValues(alpha: 0.18),
                        const Color(0xFF3B82F6).withValues(alpha: 0.0),
                      ],
                    ),
                  ),
                ),
                LineChartBarData(
                  spots: List.generate(
                    sma20Prices.length,
                    (i) => FlSpot(i.toDouble(), sma20Prices[i]),
                  ),
                  isCurved: true,
                  color: const Color(0xFFF59E0B).withValues(alpha: 0.78),
                  barWidth: 1.8,
                  dotData: const FlDotData(show: false),
                  dashArray: [6, 4],
                ),
              ],
              lineTouchData: LineTouchData(
                touchTooltipData: LineTouchTooltipData(
                  getTooltipColor: (_) =>
                      const Color(0xFF1E293B).withValues(alpha: 0.94),
                  getTooltipItems: (touchedSpots) {
                    return touchedSpots.map((spot) {
                      final idx = spot.x.toInt();
                      final date = idx < data.length ? data[idx].date : '';
                      return LineTooltipItem(
                        '$date\n\$${spot.y.toStringAsFixed(2)}',
                        const TextStyle(
                          color: Color(0xFFE2E8F0),
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                        ),
                      );
                    }).toList();
                  },
                ),
              ),
            ),
          ),
        ),
        const SizedBox(height: 10),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _legend(const Color(0xFF3B82F6), 'Close'),
            const SizedBox(width: 18),
            _legend(const Color(0xFFF59E0B), 'SMA 20'),
          ],
        ),
      ],
    );
  }

  Widget _legend(Color color, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 16,
          height: 3,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(2),
          ),
        ),
        const SizedBox(width: 6),
        Text(
          label,
          style: TextStyle(
            color: const Color(0xFF94A3B8).withValues(alpha: 0.82),
            fontSize: 11,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}
