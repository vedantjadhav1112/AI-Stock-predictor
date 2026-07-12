// ============================================================
// screens/home_screen.dart — Ticker Input & Model Selection
// ============================================================
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';
import 'analysis_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _tickerController = TextEditingController(text: 'AAPL');
  final _apiUrlController = TextEditingController();
  String _selectedModel = 'forest';
  bool _isLoadingApiUrl = true;
  bool _isSavingApiUrl = false;

  static const _apiUrlKey = 'api_base_url';
  static const _defaultApiUrl = 'http://10.124.221.204:8000';

  @override
  void initState() {
    super.initState();
    _loadApiUrl();
  }

  Future<void> _loadApiUrl() async {
    final prefs = await SharedPreferences.getInstance();
    final savedUrl = prefs.getString(_apiUrlKey) ?? _defaultApiUrl;

    if (!mounted) {
      return;
    }

    _apiUrlController.text = savedUrl;
    context.read<ApiService>().setBaseUrl(savedUrl);

    setState(() {
      _isLoadingApiUrl = false;
    });
  }

  String _normalizeApiUrl(String url) {
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

  @override
  void dispose() {
    _tickerController.dispose();
    _apiUrlController.dispose();
    super.dispose();
  }

  Future<void> _saveApiUrl() async {
    final apiUrl = _normalizeApiUrl(_apiUrlController.text);
    if (apiUrl.isEmpty) {
      return;
    }

    setState(() {
      _isSavingApiUrl = true;
    });

    try {
      final apiService = context.read<ApiService>();
      apiService.setBaseUrl(apiUrl);

      final isReachable = await apiService.healthCheck();
      if (!mounted) {
        return;
      }

      if (!isReachable) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Backend is not reachable. Check the URL and try again.'),
          ),
        );
        return;
      }

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_apiUrlKey, apiUrl);
      _apiUrlController.text = apiUrl;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('API URL saved and verified')),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isSavingApiUrl = false;
        });
      }
    }
  }

  void _analyze() async {
    final ticker = _tickerController.text.trim().toUpperCase();
    if (ticker.isEmpty) return;

    // Navigate to analysis screen, where loading will happen
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => AnalysisScreen(
          ticker: ticker,
          modelType: _selectedModel,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 48.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Hero Section
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF3B82F6).withValues(alpha: 0.15),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.auto_graph_rounded,
                  size: 48,
                  color: Color(0xFF60A5FA),
                ),
              ),
              const SizedBox(height: 32),
              Text(
                'AI Stock\nPredictor',
                style: GoogleFonts.inter(
                  fontSize: 42,
                  fontWeight: FontWeight.w800,
                  height: 1.1,
                  color: Colors.white,
                  letterSpacing: -1,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                'Machine Learning & NLP powered market analysis straight to your pocket.',
                style: TextStyle(
                  fontSize: 16,
                  color: const Color(0xFF94A3B8).withValues(alpha: 0.9),
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 40),

              const Text(
                'API SERVER URL',
                style: TextStyle(
                  color: Color(0xFF94A3B8),
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _apiUrlController,
                keyboardType: TextInputType.url,
                textInputAction: TextInputAction.done,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
                decoration: const InputDecoration(
                  hintText: 'https://your-api.example.com',
                  prefixIcon: Icon(Icons.public, color: Color(0xFF60A5FA)),
                ),
                onSubmitted: (_) => _saveApiUrl(),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton(
                  onPressed: _isLoadingApiUrl || _isSavingApiUrl
                      ? null
                      : _saveApiUrl,
                  child: _isSavingApiUrl
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Text('TEST & SAVE API URL'),
                ),
              ),
              const SizedBox(height: 40),

              // Input Form
              const Text(
                'STOCK TICKER',
                style: TextStyle(
                  color: Color(0xFF94A3B8),
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _tickerController,
                enabled: !_isLoadingApiUrl,
                textCapitalization: TextCapitalization.characters,
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 2,
                ),
                decoration: const InputDecoration(
                  hintText: 'e.g. AAPL, MSFT, TSLA',
                  prefixIcon: Icon(Icons.search, color: Color(0xFF60A5FA)),
                ),
                onSubmitted: (_) => _analyze(),
              ),
              const SizedBox(height: 24),

              const Text(
                'PREDICTION MODEL',
                style: TextStyle(
                  color: Color(0xFF94A3B8),
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 8),
              _buildModelSelector(),
              const SizedBox(height: 48),

              // Analyze Button
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: _isLoadingApiUrl ? null : _analyze,
                  child: const Text('RUN ANALYSIS'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildModelSelector() {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: const Color(0xFF1E3A5F).withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: const Color(0xFF63B3ED).withValues(alpha: 0.2),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: _modelTab('forest', 'Random Forest', Icons.park_outlined),
          ),
          Expanded(
            child: _modelTab('linear', 'Linear Reg', Icons.timeline),
          ),
        ],
      ),
    );
  }

  Widget _modelTab(String value, String label, IconData icon) {
    final isSelected = _selectedModel == value;
    return GestureDetector(
      onTap: () => setState(() => _selectedModel = value),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: isSelected
              ? const Color(0xFF3B82F6).withValues(alpha: 0.3)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          children: [
            Icon(
              icon,
              size: 20,
              color: isSelected ? const Color(0xFF60A5FA) : const Color(0xFF94A3B8),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                color: isSelected ? Colors.white : const Color(0xFF94A3B8),
                fontSize: 13,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
