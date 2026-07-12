// Basic launch smoke test for the stock predictor app.

import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:stock_predictor_app/main.dart';
import 'package:stock_predictor_app/services/api_service.dart';

void main() {
  testWidgets('home screen renders ticker analysis form', (
    WidgetTester tester,
  ) async {
    SharedPreferences.setMockInitialValues({});

    await tester.pumpWidget(
      ChangeNotifierProvider(
        create: (_) => ApiService(),
        child: const StockPredictorApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('AI Stock Predictor'), findsOneWidget);
    expect(find.text('Run Analysis'), findsOneWidget);
    expect(find.text('AAPL'), findsAtLeastNWidgets(1));
  });
}
