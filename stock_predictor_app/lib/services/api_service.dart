// ============================================================
// services/api_service.dart - HTTP Client for FastAPI Backend
// ============================================================
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/stock_analysis.dart';

class ApiService extends ChangeNotifier {
  // Default to the local backend address, but allow the app to override it.
  String _baseUrl = 'http://127.0.0.1:8000';

  /// Common headers sent with every request.
  /// The ngrok header bypasses the free-tier browser interstitial.
  static const _defaultHeaders = {
    'ngrok-skip-browser-warning': 'true',
    'Accept': 'application/json',
  };

  String get baseUrl => _baseUrl;

  String _normalizeBaseUrl(String url) {
    final trimmed = url.trim().replaceAll(RegExp(r'/+$'), '');
    if (trimmed.isEmpty) {
      return trimmed;
    }

    final hasScheme = Uri.tryParse(trimmed)?.hasScheme ?? false;
    if (hasScheme) {
      return trimmed;
    }

    return 'https://$trimmed';
  }

  void setBaseUrl(String url) {
    _baseUrl = _normalizeBaseUrl(url);
    notifyListeners();
  }

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  String? _error;
  String? get error => _error;

  StockAnalysis? _analysis;
  StockAnalysis? get analysis => _analysis;

  /// Check if the API server is reachable
  Future<bool> healthCheck() async {
    try {
      final response = await http
          .get(Uri.parse('$_baseUrl/api/health'), headers: _defaultHeaders)
          .timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  /// Run full stock analysis
  Future<StockAnalysis?> analyzeStock(
    String ticker, {
    String modelType = 'forest',
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final uri = Uri.parse(
        '$_baseUrl/api/stock/$ticker/analysis?model_type=$modelType',
      );
      final response = await http
          .get(uri, headers: _defaultHeaders)
          .timeout(const Duration(seconds: 120));

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body);
        _analysis = StockAnalysis.fromJson(json);
        _isLoading = false;
        notifyListeners();
        return _analysis;
      } else {
        final errorBody = jsonDecode(response.body);
        _error = errorBody['detail'] ?? 'Analysis failed';
        _isLoading = false;
        notifyListeners();
        return null;
      }
    } catch (e) {
      _error = 'Connection error: $e';
      _isLoading = false;
      notifyListeners();
      return null;
    }
  }

  /// Get current stock price (lightweight)
  Future<Map<String, dynamic>?> getPrice(String ticker) async {
    try {
      final response = await http
          .get(Uri.parse('$_baseUrl/api/stock/$ticker/price'), headers: _defaultHeaders)
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  /// Get news and sentiment only
  Future<Map<String, dynamic>?> getNews(String ticker) async {
    try {
      final response = await http
          .get(Uri.parse('$_baseUrl/api/stock/$ticker/news'), headers: _defaultHeaders)
          .timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  void clearAnalysis() {
    _analysis = null;
    _error = null;
    _isLoading = false;
    notifyListeners();
  }
}
