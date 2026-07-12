// ============================================================
// models/stock_analysis.dart — Data model for full analysis
// ============================================================

class StockAnalysis {
  final String ticker;
  final double currentPrice;
  final double predictedPrice;
  final double priceChange;
  final double priceChangePct;
  final double confidence;
  final String modelType;
  final bool cachedModel;
  final CompanyInfo company;
  final ModelMetrics metrics;
  final TechnicalIndicators technical;
  final List<FeatureImportance> featureImportance;
  final SentimentResult sentiment;
  final String newsSummary;
  final List<NewsArticle> articles;
  final List<ChartDataPoint> chartData;

  StockAnalysis({
    required this.ticker,
    required this.currentPrice,
    required this.predictedPrice,
    required this.priceChange,
    required this.priceChangePct,
    required this.confidence,
    required this.modelType,
    required this.cachedModel,
    required this.company,
    required this.metrics,
    required this.technical,
    required this.featureImportance,
    required this.sentiment,
    required this.newsSummary,
    required this.articles,
    required this.chartData,
  });

  factory StockAnalysis.fromJson(Map<String, dynamic> json) {
    return StockAnalysis(
      ticker: json['ticker'] ?? '',
      currentPrice: (json['current_price'] ?? 0).toDouble(),
      predictedPrice: (json['predicted_price'] ?? 0).toDouble(),
      priceChange: (json['price_change'] ?? 0).toDouble(),
      priceChangePct: (json['price_change_pct'] ?? 0).toDouble(),
      confidence: (json['confidence'] ?? 0).toDouble(),
      modelType: json['model_type'] ?? 'forest',
      cachedModel: json['cached_model'] ?? false,
      company: CompanyInfo.fromJson(json['company'] ?? {}),
      metrics: ModelMetrics.fromJson(json['metrics'] ?? {}),
      technical: TechnicalIndicators.fromJson(json['technical'] ?? {}),
      featureImportance: (json['feature_importance'] as List? ?? [])
          .map((e) => FeatureImportance.fromJson(e))
          .toList(),
      sentiment: SentimentResult.fromJson(json['sentiment'] ?? {}),
      newsSummary: json['news_summary'] ?? '',
      articles: (json['articles'] as List? ?? [])
          .map((e) => NewsArticle.fromJson(e))
          .toList(),
      chartData: (json['chart_data'] as List? ?? [])
          .map((e) => ChartDataPoint.fromJson(e))
          .toList(),
    );
  }
}

class CompanyInfo {
  final String name;
  final String currency;
  final num marketCap;

  CompanyInfo({
    required this.name,
    required this.currency,
    required this.marketCap,
  });

  factory CompanyInfo.fromJson(Map<String, dynamic> json) {
    return CompanyInfo(
      name: json['name'] ?? '',
      currency: json['currency'] ?? 'USD',
      marketCap: json['market_cap'] ?? 0,
    );
  }

  String get formattedMarketCap {
    if (marketCap >= 1e12) return '\$${(marketCap / 1e12).toStringAsFixed(2)}T';
    if (marketCap >= 1e9) return '\$${(marketCap / 1e9).toStringAsFixed(2)}B';
    if (marketCap >= 1e6) return '\$${(marketCap / 1e6).toStringAsFixed(2)}M';
    return '\$${marketCap.toStringAsFixed(0)}';
  }
}

class ModelMetrics {
  final double mae;
  final double rmse;
  final double r2;
  final double mape;

  ModelMetrics({
    required this.mae,
    required this.rmse,
    required this.r2,
    required this.mape,
  });

  factory ModelMetrics.fromJson(Map<String, dynamic> json) {
    return ModelMetrics(
      mae: (json['MAE'] ?? 0).toDouble(),
      rmse: (json['RMSE'] ?? 0).toDouble(),
      r2: (json['R2'] ?? 0).toDouble(),
      mape: (json['MAPE'] ?? 0).toDouble(),
    );
  }
}

class TechnicalIndicators {
  final double rsi;
  final double sma5;
  final double sma20;
  final double volatility10;
  final double closeToSma20;
  final double dailyReturn;
  final int volume;

  TechnicalIndicators({
    required this.rsi,
    required this.sma5,
    required this.sma20,
    required this.volatility10,
    required this.closeToSma20,
    required this.dailyReturn,
    required this.volume,
  });

  factory TechnicalIndicators.fromJson(Map<String, dynamic> json) {
    return TechnicalIndicators(
      rsi: (json['rsi'] ?? 0).toDouble(),
      sma5: (json['sma_5'] ?? 0).toDouble(),
      sma20: (json['sma_20'] ?? 0).toDouble(),
      volatility10: (json['volatility_10'] ?? 0).toDouble(),
      closeToSma20: (json['close_to_sma20'] ?? 0).toDouble(),
      dailyReturn: (json['daily_return'] ?? 0).toDouble(),
      volume: (json['volume'] ?? 0).toInt(),
    );
  }
}

class FeatureImportance {
  final String name;
  final double score;

  FeatureImportance({required this.name, required this.score});

  factory FeatureImportance.fromJson(Map<String, dynamic> json) {
    return FeatureImportance(
      name: json['name'] ?? '',
      score: (json['score'] ?? 0).toDouble(),
    );
  }
}

class SentimentResult {
  final String overallSentiment;
  final double confidence;
  final double positivePct;
  final double negativePct;
  final double neutralPct;
  final List<SentimentDetail> details;

  SentimentResult({
    required this.overallSentiment,
    required this.confidence,
    required this.positivePct,
    required this.negativePct,
    required this.neutralPct,
    required this.details,
  });

  factory SentimentResult.fromJson(Map<String, dynamic> json) {
    return SentimentResult(
      overallSentiment: json['overall_sentiment'] ?? 'Neutral',
      confidence: (json['confidence'] ?? 0).toDouble(),
      positivePct: (json['positive_pct'] ?? 0).toDouble(),
      negativePct: (json['negative_pct'] ?? 0).toDouble(),
      neutralPct: (json['neutral_pct'] ?? 0).toDouble(),
      details: (json['details'] as List? ?? [])
          .map((e) => SentimentDetail.fromJson(e))
          .toList(),
    );
  }
}

class SentimentDetail {
  final String headline;
  final String sentiment;
  final double confidence;

  SentimentDetail({
    required this.headline,
    required this.sentiment,
    required this.confidence,
  });

  factory SentimentDetail.fromJson(Map<String, dynamic> json) {
    return SentimentDetail(
      headline: json['headline'] ?? '',
      sentiment: json['sentiment'] ?? 'Neutral',
      confidence: (json['confidence'] ?? 0).toDouble(),
    );
  }
}

class NewsArticle {
  final String title;
  final String publisher;
  final String link;
  final String published;

  NewsArticle({
    required this.title,
    required this.publisher,
    required this.link,
    required this.published,
  });

  factory NewsArticle.fromJson(Map<String, dynamic> json) {
    return NewsArticle(
      title: json['title'] ?? '',
      publisher: json['publisher'] ?? '',
      link: json['link'] ?? '',
      published: json['published'] ?? '',
    );
  }
}

class ChartDataPoint {
  final String date;
  final double open;
  final double high;
  final double low;
  final double close;
  final int volume;
  final double sma5;
  final double sma20;
  final double rsi;

  ChartDataPoint({
    required this.date,
    required this.open,
    required this.high,
    required this.low,
    required this.close,
    required this.volume,
    required this.sma5,
    required this.sma20,
    required this.rsi,
  });

  factory ChartDataPoint.fromJson(Map<String, dynamic> json) {
    return ChartDataPoint(
      date: json['date'] ?? '',
      open: (json['Open'] ?? 0).toDouble(),
      high: (json['High'] ?? 0).toDouble(),
      low: (json['Low'] ?? 0).toDouble(),
      close: (json['Close'] ?? 0).toDouble(),
      volume: (json['Volume'] ?? 0).toInt(),
      sma5: (json['SMA_5'] ?? 0).toDouble(),
      sma20: (json['SMA_20'] ?? 0).toDouble(),
      rsi: (json['RSI'] ?? 0).toDouble(),
    );
  }
}
