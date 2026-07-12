// ============================================================
// widgets/stock_chart.dart — Price Line Chart
// ============================================================
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import '../models/stock_analysis.dart';

class StockChart extends StatelessWidget {
  final List<ChartDataPoint> data;
  final String ticker;

  const StockChart({
    super.key,
    required this.data,
    required this.ticker,
  });

  @override
  Widget build(BuildContext context) {
    if (data.isEmpty) {
      return const Center(child: Text('No chart data available'));
    }

    final closePrices =
        data.map((e) => e.close).toList();
    final sma20Prices =
        data.map((e) => e.sma20).toList();
    final minY = closePrices.reduce((a, b) => a < b ? a : b) * 0.97;
    final maxY = closePrices.reduce((a, b) => a > b ? a : b) * 1.03;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '$ticker — Price History',
          style: const TextStyle(
            color: Color(0xFFE2E8F0),
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 16),
        SizedBox(
          height: 250,
          child: LineChart(
            LineChartData(
              minY: minY,
              maxY: maxY,
              gridData: FlGridData(
                show: true,
                drawVerticalLine: false,
                horizontalInterval: (maxY - minY) / 5,
                getDrawingHorizontalLine: (value) => FlLine(
                  color: const Color(0xFF63B3ED).withValues(alpha: 0.08),
                  strokeWidth: 1,
                ),
              ),
              titlesData: FlTitlesData(
                topTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false)),
                rightTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false)),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    interval: (data.length / 4).ceilToDouble(),
                    getTitlesWidget: (value, meta) {
                      final idx = value.toInt();
                      if (idx < 0 || idx >= data.length) {
                        return const SizedBox.shrink();
                      }
                      final dateStr = data[idx].date;
                      final parts = dateStr.split('-');
                      return Padding(
                        padding: const EdgeInsets.only(top: 8),
                        child: Text(
                          '${parts[1]}/${parts[2]}',
                          style: TextStyle(
                            color: const Color(0xFF94A3B8).withValues(alpha: 0.7),
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
                    reservedSize: 55,
                    getTitlesWidget: (value, meta) {
                      return Text(
                        '\$${value.toStringAsFixed(0)}',
                        style: TextStyle(
                          color: const Color(0xFF94A3B8).withValues(alpha: 0.7),
                          fontSize: 10,
                        ),
                      );
                    },
                  ),
                ),
              ),
              borderData: FlBorderData(show: false),
              lineBarsData: [
                // Close price line
                LineChartBarData(
                  spots: List.generate(
                    closePrices.length,
                    (i) => FlSpot(i.toDouble(), closePrices[i]),
                  ),
                  isCurved: true,
                  color: const Color(0xFF3B82F6),
                  barWidth: 2.5,
                  dotData: const FlDotData(show: false),
                  belowBarData: BarAreaData(
                    show: true,
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [
                        const Color(0xFF3B82F6).withValues(alpha: 0.15),
                        const Color(0xFF3B82F6).withValues(alpha: 0.0),
                      ],
                    ),
                  ),
                ),
                // SMA 20 line
                LineChartBarData(
                  spots: List.generate(
                    sma20Prices.length,
                    (i) => FlSpot(i.toDouble(), sma20Prices[i]),
                  ),
                  isCurved: true,
                  color: const Color(0xFF60A5FA).withValues(alpha: 0.5),
                  barWidth: 1.5,
                  dotData: const FlDotData(show: false),
                  dashArray: [6, 4],
                ),
              ],
              lineTouchData: LineTouchData(
                touchTooltipData: LineTouchTooltipData(
                  getTooltipColor: (_) =>
                      const Color(0xFF1E293B).withValues(alpha: 0.9),
                  getTooltipItems: (touchedSpots) {
                    return touchedSpots.map((spot) {
                      final idx = spot.x.toInt();
                      final date = idx < data.length ? data[idx].date : '';
                      return LineTooltipItem(
                        '$date\n\$${spot.y.toStringAsFixed(2)}',
                        const TextStyle(
                          color: Color(0xFFE2E8F0),
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      );
                    }).toList();
                  },
                ),
              ),
            ),
          ),
        ),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _legend(const Color(0xFF3B82F6), 'Close Price'),
            const SizedBox(width: 20),
            _legend(const Color(0xFF60A5FA), 'SMA 20'),
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
            color: const Color(0xFF94A3B8).withValues(alpha: 0.8),
            fontSize: 11,
          ),
        ),
      ],
    );
  }
}
