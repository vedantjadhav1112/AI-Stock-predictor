// ============================================================
// screens/analysis_screen.dart - Full ML and NLP results
// ============================================================
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/stock_analysis.dart';
import '../services/api_service.dart';
import '../widgets/glass_card.dart';
import '../widgets/metric_card.dart';
import '../widgets/stock_chart.dart';
import '../widgets/sentiment_bar.dart';
import '../widgets/news_list.dart';

class AnalysisScreen extends StatefulWidget {
  final String ticker;
  final String modelType;

  const AnalysisScreen({
    super.key,
    required this.ticker,
    required this.modelType,
  });

  @override
  State<AnalysisScreen> createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);

    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ApiService>().analyzeStock(
        widget.ticker,
        modelType: widget.modelType,
      );
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 0,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(widget.ticker.toUpperCase()),
            Text(
              widget.modelType == 'forest'
                  ? 'Random Forest model'
                  : 'Linear model',
              style: const TextStyle(
                color: Color(0xFF94A3B8),
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: const Color(0xFF60A5FA),
          indicatorWeight: 3,
          labelColor: Colors.white,
          unselectedLabelColor: const Color(0xFF94A3B8),
          tabs: const [
            Tab(text: 'Overview'),
            Tab(text: 'Technical'),
            Tab(text: 'News'),
          ],
        ),
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFF0F172A), Color(0xFF111827)],
          ),
        ),
        child: Consumer<ApiService>(
          builder: (context, api, child) {
            if (api.isLoading) {
              return _buildLoadingState();
            }

            if (api.error != null) {
              return _buildErrorState(api.error!);
            }

            final analysis = api.analysis;
            if (analysis == null) {
              return const SizedBox.shrink();
            }

            return TabBarView(
              controller: _tabController,
              children: [
                RefreshIndicator(
                  onRefresh: () => api.analyzeStock(
                    widget.ticker,
                    modelType: widget.modelType,
                  ),
                  child: _overviewTab(analysis),
                ),
                _technicalTab(analysis),
                _newsTab(analysis),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildLoadingState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: GlassCard(
          margin: EdgeInsets.zero,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const SizedBox(
                width: 42,
                height: 42,
                child: CircularProgressIndicator(
                  color: Color(0xFF60A5FA),
                  strokeWidth: 3,
                ),
              ),
              const SizedBox(height: 20),
              Text(
                'Analyzing ${widget.ticker.toUpperCase()}',
                style: const TextStyle(
                  color: Color(0xFFE2E8F0),
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                widget.modelType == 'forest'
                    ? 'Training or loading the Random Forest model'
                    : 'Training or loading the Linear Regression model',
                textAlign: TextAlign.center,
                style: const TextStyle(color: Color(0xFF94A3B8), height: 1.4),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildErrorState(String message) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: GlassCard(
          margin: EdgeInsets.zero,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.error_outline,
                color: Color(0xFFEF4444),
                size: 48,
              ),
              const SizedBox(height: 14),
              const Text(
                'Analysis failed',
                style: TextStyle(
                  color: Color(0xFFE2E8F0),
                  fontSize: 19,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                message,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Color(0xFF94A3B8), height: 1.4),
              ),
              const SizedBox(height: 22),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.arrow_back_rounded),
                  label: const Text('Back'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _overviewTab(StockAnalysis analysis) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildHeaderSummary(analysis),
        _metricGrid([
          MetricCard(
            label: 'Current price',
            value: '\$${analysis.currentPrice.toStringAsFixed(2)}',
            icon: Icons.attach_money_rounded,
          ),
          MetricCard(
            label: 'Predicted T+1',
            value: '\$${analysis.predictedPrice.toStringAsFixed(2)}',
            delta: _formatSignedPct(analysis.priceChangePct),
            positive: analysis.priceChange >= 0,
            icon: Icons.online_prediction_rounded,
          ),
          MetricCard(
            label: 'Confidence',
            value: '${analysis.confidence.toStringAsFixed(0)}%',
            positive: analysis.confidence >= 70,
            icon: Icons.analytics_outlined,
          ),
          MetricCard(
            label: 'R2 score',
            value: analysis.metrics.r2.toStringAsFixed(3),
            positive: analysis.metrics.r2 >= 0,
            icon: Icons.verified_outlined,
          ),
        ]),
        GlassCard(
          child: StockChart(ticker: widget.ticker, data: analysis.chartData),
        ),
        _modelQualityCard(analysis),
      ],
    );
  }

  Widget _technicalTab(StockAnalysis analysis) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _sectionTitle('Latest Indicators'),
        const SizedBox(height: 12),
        _metricGrid([
          MetricCard(
            label: 'RSI 14',
            value: analysis.technical.rsi.toStringAsFixed(1),
            delta: _rsiStatus(analysis.technical.rsi),
            positive: analysis.technical.rsi < 70,
            icon: Icons.speed_rounded,
          ),
          MetricCard(
            label: 'Volatility 10d',
            value: '${analysis.technical.volatility10.toStringAsFixed(2)}%',
            icon: Icons.show_chart_rounded,
          ),
          MetricCard(
            label: 'SMA 5',
            value: '\$${analysis.technical.sma5.toStringAsFixed(2)}',
            icon: Icons.timeline_rounded,
          ),
          MetricCard(
            label: 'SMA 20',
            value: '\$${analysis.technical.sma20.toStringAsFixed(2)}',
            icon: Icons.stacked_line_chart_rounded,
          ),
        ]),
        _technicalCallout(analysis),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Model Drivers',
                style: TextStyle(
                  color: Color(0xFFE2E8F0),
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 16),
              _featureImportanceList(analysis.featureImportance),
            ],
          ),
        ),
      ],
    );
  }

  Widget _newsTab(StockAnalysis analysis) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'News Sentiment',
                style: TextStyle(
                  color: Color(0xFFE2E8F0),
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 16),
              SentimentBar(sentiment: analysis.sentiment),
              const SizedBox(height: 18),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFF111827).withValues(alpha: 0.65),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: const Color(0xFF64748B).withValues(alpha: 0.18),
                  ),
                ),
                child: Text(
                  analysis.newsSummary.isEmpty
                      ? 'No summary returned.'
                      : analysis.newsSummary,
                  style: const TextStyle(
                    color: Color(0xFFCBD5E1),
                    fontSize: 14,
                    height: 1.45,
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 4),
        _sectionTitle('Recent Articles'),
        const SizedBox(height: 12),
        GlassCard(
          padding: const EdgeInsets.all(16),
          child: NewsList(articles: analysis.articles),
        ),
      ],
    );
  }

  Widget _buildHeaderSummary(StockAnalysis analysis) {
    final isUp = analysis.priceChange >= 0;
    return GlassCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: (isUp ? const Color(0xFF22C55E) : const Color(0xFFEF4444))
                  .withValues(alpha: 0.16),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(
              isUp ? Icons.trending_up_rounded : Icons.trending_down_rounded,
              color: isUp ? const Color(0xFF22C55E) : const Color(0xFFEF4444),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  analysis.company.name.isEmpty
                      ? analysis.ticker
                      : analysis.company.name,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: Color(0xFFE2E8F0),
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    _InfoPill(label: analysis.company.formattedMarketCap),
                    _InfoPill(label: analysis.company.currency),
                    _InfoPill(
                      label: analysis.cachedModel
                          ? 'Cached model'
                          : 'Fresh model',
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _modelQualityCard(StockAnalysis analysis) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Model Quality',
            style: TextStyle(
              color: Color(0xFFE2E8F0),
              fontSize: 16,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 14),
          _qualityRow('MAE', '\$${analysis.metrics.mae.toStringAsFixed(2)}'),
          _qualityRow('RMSE', '\$${analysis.metrics.rmse.toStringAsFixed(2)}'),
          _qualityRow('MAPE', '${analysis.metrics.mape.toStringAsFixed(2)}%'),
        ],
      ),
    );
  }

  Widget _technicalCallout(StockAnalysis analysis) {
    final closeToSma = analysis.technical.closeToSma20;
    final abovePct = (closeToSma - 1) * 100;
    final status = closeToSma >= 1.02
        ? 'Price is ${abovePct.toStringAsFixed(1)}% above the 20-day average.'
        : closeToSma <= 0.98
        ? 'Price is ${abovePct.abs().toStringAsFixed(1)}% below the 20-day average.'
        : 'Price is trading near the 20-day average.';

    return GlassCard(
      child: Row(
        children: [
          const Icon(Icons.insights_rounded, color: Color(0xFF60A5FA)),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              status,
              style: const TextStyle(color: Color(0xFFCBD5E1), height: 1.4),
            ),
          ),
        ],
      ),
    );
  }

  Widget _featureImportanceList(List<FeatureImportance> items) {
    if (items.isEmpty) {
      return const Text(
        'No feature importance returned.',
        style: TextStyle(color: Color(0xFF94A3B8)),
      );
    }

    final maxScore = items
        .map((item) => item.score.abs())
        .fold<double>(0, math.max);

    return Column(
      children: items.map((feature) {
        final normalized = maxScore == 0
            ? 0.0
            : (feature.score.abs() / maxScore).clamp(0.0, 1.0);
        return Padding(
          padding: const EdgeInsets.only(bottom: 14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      feature.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Color(0xFFCBD5E1),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    feature.score.toStringAsFixed(4),
                    style: const TextStyle(
                      color: Color(0xFF94A3B8),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              ClipRRect(
                borderRadius: BorderRadius.circular(5),
                child: LinearProgressIndicator(
                  value: normalized,
                  minHeight: 7,
                  backgroundColor: const Color(
                    0xFF1E3A5F,
                  ).withValues(alpha: 0.55),
                  valueColor: const AlwaysStoppedAnimation<Color>(
                    Color(0xFF3B82F6),
                  ),
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _metricGrid(List<Widget> children) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth >= 620 ? 4 : 2;
        final gap = 12.0;
        final width = (constraints.maxWidth - gap * (columns - 1)) / columns;

        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: children
              .map((child) => SizedBox(width: width, child: child))
              .toList(),
        );
      },
    );
  }

  Widget _qualityRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          Expanded(
            child: Text(
              label,
              style: const TextStyle(color: Color(0xFF94A3B8)),
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              color: Color(0xFFE2E8F0),
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }

  Widget _sectionTitle(String label) {
    return Text(
      label.toUpperCase(),
      style: const TextStyle(
        color: Color(0xFF94A3B8),
        fontSize: 11,
        fontWeight: FontWeight.w700,
        letterSpacing: 0,
      ),
    );
  }

  String _formatSignedPct(double value) {
    return '${value >= 0 ? '+' : ''}${value.toStringAsFixed(2)}%';
  }

  String _rsiStatus(double rsi) {
    if (rsi > 70) return 'Overbought';
    if (rsi < 30) return 'Oversold';
    return 'Neutral';
  }
}

class _InfoPill extends StatelessWidget {
  final String label;

  const _InfoPill({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: const Color(0xFF111827).withValues(alpha: 0.74),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: const Color(0xFF64748B).withValues(alpha: 0.18),
        ),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: Color(0xFFCBD5E1),
          fontSize: 12,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
