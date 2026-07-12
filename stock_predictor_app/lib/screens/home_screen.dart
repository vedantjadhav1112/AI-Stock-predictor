// ============================================================
// screens/home_screen.dart - Ticker input and API settings
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
  static const _defaultApiUrl = 'http://127.0.0.1:8000';
  static const _popularTickers = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'GOOGL'];

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
    return hasScheme ? trimmed : 'https://$trimmed';
  }

  @override
  void dispose() {
    _tickerController.dispose();
    _apiUrlController.dispose();
    super.dispose();
  }

  Future<void> _saveApiUrl() async {
    final apiUrl = _normalizeApiUrl(_apiUrlController.text);
    if (apiUrl.isEmpty || _isSavingApiUrl) {
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
            content: Text('Backend is not reachable. Check the URL.'),
          ),
        );
        return;
      }

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_apiUrlKey, apiUrl);
      _apiUrlController.text = apiUrl;

      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('API URL saved')));
    } finally {
      if (mounted) {
        setState(() {
          _isSavingApiUrl = false;
        });
      }
    }
  }

  void _analyze() {
    final ticker = _tickerController.text.trim().toUpperCase();
    if (ticker.isEmpty) {
      return;
    }

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) =>
            AnalysisScreen(ticker: ticker, modelType: _selectedModel),
      ),
    );
  }

  void _setTicker(String ticker) {
    _tickerController.text = ticker;
    _tickerController.selection = TextSelection.collapsed(
      offset: ticker.length,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFF0B1120), Color(0xFF0F172A), Color(0xFF111827)],
          ),
        ),
        child: SafeArea(
          child: LayoutBuilder(
            builder: (context, constraints) {
              final maxWidth = constraints.maxWidth > 620
                  ? 560.0
                  : double.infinity;

              return Center(
                child: ConstrainedBox(
                  constraints: BoxConstraints(maxWidth: maxWidth),
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.fromLTRB(20, 28, 20, 28),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildHeader(),
                        const SizedBox(height: 24),
                        _buildAnalysisPanel(),
                        const SizedBox(height: 16),
                        _buildConnectionPanel(),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Container(
          width: 52,
          height: 52,
          decoration: BoxDecoration(
            color: const Color(0xFF2563EB).withValues(alpha: 0.16),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: const Color(0xFF60A5FA).withValues(alpha: 0.22),
            ),
          ),
          child: const Icon(
            Icons.auto_graph_rounded,
            color: Color(0xFF60A5FA),
            size: 30,
          ),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'AI Stock Predictor',
                style: GoogleFonts.inter(
                  color: Colors.white,
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  height: 1.05,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                'Forecasts, technicals, and market sentiment',
                style: TextStyle(
                  color: const Color(0xFF94A3B8).withValues(alpha: 0.9),
                  fontSize: 13,
                  height: 1.35,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildAnalysisPanel() {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: _panelDecoration(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _sectionLabel('Stock ticker'),
          const SizedBox(height: 8),
          TextField(
            controller: _tickerController,
            enabled: !_isLoadingApiUrl,
            textCapitalization: TextCapitalization.characters,
            textInputAction: TextInputAction.search,
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w800,
              letterSpacing: 0,
            ),
            decoration: const InputDecoration(
              hintText: 'AAPL',
              prefixIcon: Icon(Icons.search, color: Color(0xFF60A5FA)),
            ),
            onSubmitted: (_) => _analyze(),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _popularTickers
                .map(
                  (ticker) => _QuickTickerChip(
                    ticker: ticker,
                    onTap: () => _setTicker(ticker),
                  ),
                )
                .toList(),
          ),
          const SizedBox(height: 24),
          _sectionLabel('Prediction model'),
          const SizedBox(height: 8),
          _buildModelSelector(),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            height: 54,
            child: ElevatedButton.icon(
              onPressed: _isLoadingApiUrl ? null : _analyze,
              icon: const Icon(Icons.play_arrow_rounded),
              label: const Text('Run Analysis'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildConnectionPanel() {
    return Container(
      decoration: _panelDecoration(),
      child: Material(
        color: Colors.transparent,
        child: Theme(
          data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
          child: ExpansionTile(
          tilePadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 4),
          childrenPadding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
          leading: const Icon(Icons.dns_outlined, color: Color(0xFF60A5FA)),
          title: const Text(
            'API Connection',
            style: TextStyle(
              fontWeight: FontWeight.w700,
              color: Color(0xFFE2E8F0),
            ),
          ),
          subtitle: Consumer<ApiService>(
            builder: (context, api, _) => Text(
              api.baseUrl,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 12),
            ),
          ),
          children: [
            TextField(
              controller: _apiUrlController,
              keyboardType: TextInputType.url,
              textInputAction: TextInputAction.done,
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
              decoration: const InputDecoration(
                hintText: 'http://127.0.0.1:8000',
                prefixIcon: Icon(Icons.public, color: Color(0xFF60A5FA)),
              ),
              onSubmitted: (_) => _saveApiUrl(),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              height: 46,
              child: OutlinedButton.icon(
                onPressed: _isLoadingApiUrl || _isSavingApiUrl
                    ? null
                    : _saveApiUrl,
                icon: _isSavingApiUrl
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.check_circle_outline),
                label: Text(_isSavingApiUrl ? 'Checking' : 'Test and Save'),
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
        color: const Color(0xFF111827).withValues(alpha: 0.62),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: const Color(0xFF63B3ED).withValues(alpha: 0.16),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: _modelTab(
              'forest',
              'Random Forest',
              Icons.account_tree_outlined,
            ),
          ),
          Expanded(
            child: _modelTab('linear', 'Linear', Icons.timeline_rounded),
          ),
        ],
      ),
    );
  }

  Widget _modelTab(String value, String label, IconData icon) {
    final isSelected = _selectedModel == value;
    return Semantics(
      button: true,
      selected: isSelected,
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: () => setState(() => _selectedModel = value),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 10),
          decoration: BoxDecoration(
            color: isSelected ? const Color(0xFF2563EB) : Colors.transparent,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 18,
                color: isSelected ? Colors.white : const Color(0xFF94A3B8),
              ),
              const SizedBox(width: 8),
              Flexible(
                child: Text(
                  label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: isSelected ? Colors.white : const Color(0xFF94A3B8),
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _sectionLabel(String label) {
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

  BoxDecoration _panelDecoration() {
    return BoxDecoration(
      color: const Color(0xFF172033).withValues(alpha: 0.88),
      borderRadius: BorderRadius.circular(8),
      border: Border.all(
        color: const Color(0xFF63B3ED).withValues(alpha: 0.16),
      ),
      boxShadow: [
        BoxShadow(
          color: Colors.black.withValues(alpha: 0.22),
          blurRadius: 24,
          offset: const Offset(0, 12),
        ),
      ],
    );
  }
}

class _QuickTickerChip extends StatelessWidget {
  final String ticker;
  final VoidCallback onTap;

  const _QuickTickerChip({required this.ticker, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return ActionChip(
      onPressed: onTap,
      avatar: const Icon(Icons.add_rounded, size: 16, color: Color(0xFF60A5FA)),
      label: Text(ticker),
      labelStyle: const TextStyle(
        color: Color(0xFFE2E8F0),
        fontWeight: FontWeight.w700,
      ),
      backgroundColor: const Color(0xFF1E293B),
      side: BorderSide(color: const Color(0xFF63B3ED).withValues(alpha: 0.16)),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
    );
  }
}

