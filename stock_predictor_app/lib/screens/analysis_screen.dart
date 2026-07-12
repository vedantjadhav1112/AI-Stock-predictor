// ============================================================
// screens/analysis_screen.dart — Full ML & NLP Results
// ============================================================
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
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
    
    // Fetch data after the first frame
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
        title: Text(widget.ticker.toUpperCase()),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: const Color(0xFF60A5FA),
          indicatorWeight: 3,
          labelColor: Colors.white,
          unselectedLabelColor: const Color(0xFF94A3B8),
          tabs: const [
            Tab(text: 'OVERVIEW'),
            Tab(text: 'TECHNICAL'),
            Tab(text: 'NEWS'),
          ],
        ),
      ),
      body: Consumer<ApiService>(
        builder: (context, api, child) {
          if (api.isLoading) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const CircularProgressIndicator(
                    color: Color(0xFF60A5FA),
                  ),
                  const SizedBox(height: 24),
                  Text(
                    'Running ${widget.modelType == 'forest' ? 'Random Forest' : 'Linear'} pipeline...',
                    style: TextStyle(
                      color: const Color(0xFF94A3B8).withValues(alpha: 0.8),
                    ),
                  ),
                ],
              ),
            );
          }

          if (api.error != null) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(32.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.error_outline,
                        color: Color(0xFFEF4444), size: 64),
                    const SizedBox(height: 16),
                    Text(
                      'Analysis Failed',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      api.error!,
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: Color(0xFF94A3B8)),
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('GO BACK'),
                    ),
                  ],
                ),
              ),
            );
          }

          final analysis = api.analysis;
          if (analysis == null) {
            return const SizedBox.shrink();
          }

          return TabBarView(
            controller: _tabController,
            children: [
              // --- TAB 1: OVERVIEW ---
              RefreshIndicator(
                onRefresh: () => api.analyzeStock(widget.ticker,
                    modelType: widget.modelType),
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    GlassCard(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            analysis.company.name,
                            style: const TextStyle(
                              color: Color(0xFFE2E8F0),
                              fontSize: 18,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Market Cap: ${analysis.company.formattedMarketCap}',
                            style: const TextStyle(
                              color: Color(0xFF94A3B8),
                              fontSize: 13,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Row(
                      children: [
                        Expanded(
                          child: MetricCard(
                            label: 'Current Price',
                            value: '\$${analysis.currentPrice.toStringAsFixed(2)}',
                            icon: Icons.attach_money,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: MetricCard(
                            label: 'Predicted (T+1)',
                            value: '\$${analysis.predictedPrice.toStringAsFixed(2)}',
                            delta: '${analysis.priceChange > 0 ? '+' : ''}${analysis.priceChangePct.toStringAsFixed(2)}%',
                            positive: analysis.priceChange >= 0,
                            icon: Icons.online_prediction,
                          ),
                        ),
                      ],
                    ),
                    Row(
                      children: [
                        Expanded(
                          child: MetricCard(
                            label: 'Model Accuracy (R²)',
                            value: analysis.metrics.r2.toStringAsFixed(3),
                            icon: Icons.check_circle_outline,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: MetricCard(
                            label: 'Confidence',
                            value: '${analysis.confidence.toStringAsFixed(0)}%',
                            positive: analysis.confidence > 70,
                            icon: Icons.analytics_outlined,
                          ),
                        ),
                      ],
                    ),
                    GlassCard(
                      child: StockChart(
                        ticker: widget.ticker,
                        data: analysis.chartData,
                      ),
                    ),
                  ],
                ),
              ),

              // --- TAB 2: TECHNICAL ---
              ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  const Text(
                    'INDICATORS (LATEST)',
                    style: TextStyle(
                      color: Color(0xFF94A3B8),
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 1.2,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: MetricCard(
                          label: 'RSI (14)',
                          value: analysis.technical.rsi.toStringAsFixed(1),
                          delta: analysis.technical.rsi > 70
                              ? 'Overbought'
                              : (analysis.technical.rsi < 30
                                  ? 'Oversold'
                                  : 'Neutral'),
                          positive: analysis.technical.rsi < 70,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: MetricCard(
                          label: 'Volatility (10d)',
                          value: '${analysis.technical.volatility10.toStringAsFixed(2)}%',
                        ),
                      ),
                    ],
                  ),
                  GlassCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Top Features (Model Importance)',
                          style: TextStyle(
                            color: Color(0xFFE2E8F0),
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 16),
                        ...analysis.featureImportance.map((f) => Padding(
                              padding: const EdgeInsets.only(bottom: 12),
                              child: Row(
                                children: [
                                  SizedBox(
                                    width: 120,
                                    child: Text(
                                      f.name,
                                      style: const TextStyle(
                                          color: Color(0xFF94A3B8)),
                                    ),
                                  ),
                                  Expanded(
                                    child: LinearProgressIndicator(
                                      value: f.score,
                                      backgroundColor: const Color(0xFF1E3A5F)
                                          .withValues(alpha: 0.5),
                                      valueColor:
                                          const AlwaysStoppedAnimation<Color>(
                                              Color(0xFF3B82F6)),
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Text(
                                    '${(f.score * 100).toStringAsFixed(1)}%',
                                    style: const TextStyle(
                                      color: Color(0xFFE2E8F0),
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                              ),
                            )),
                      ],
                    ),
                  ),
                ],
              ),

              // --- TAB 3: NEWS ---
              ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  GlassCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'FinBERT Sentiment',
                          style: TextStyle(
                            color: Color(0xFFE2E8F0),
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 16),
                        SentimentBar(sentiment: analysis.sentiment),
                        const SizedBox(height: 20),
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: const Color(0xFF1E293B).withValues(alpha: 0.5),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                                color: const Color(0xFF64748B).withValues(alpha: 0.2)),
                          ),
                          child: Text(
                            analysis.newsSummary,
                            style: const TextStyle(
                              color: Color(0xFFCBD5E1),
                              fontSize: 14,
                              height: 1.5,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'RECENT ARTICLES',
                    style: TextStyle(
                      color: Color(0xFF94A3B8),
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 1.2,
                    ),
                  ),
                  const SizedBox(height: 12),
                  GlassCard(
                    padding: const EdgeInsets.all(16),
                    child: NewsList(articles: analysis.articles),
                  ),
                ],
              ),
            ],
          );
        },
      ),
    );
  }
}
