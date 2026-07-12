// ============================================================
// widgets/news_list.dart — News Articles List
// ============================================================
import 'package:flutter/material.dart';
import '../models/stock_analysis.dart';

class NewsList extends StatelessWidget {
  final List<NewsArticle> articles;

  const NewsList({super.key, required this.articles});

  @override
  Widget build(BuildContext context) {
    if (articles.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(20),
          child: Text('No recent news articles found.'),
        ),
      );
    }

    return ListView.separated(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: articles.length,
      separatorBuilder: (context, index) => Divider(
        color: const Color(0xFF63B3ED).withValues(alpha: 0.1),
        height: 24,
      ),
      itemBuilder: (context, index) {
        final article = articles[index];
        return InkWell(
          onTap: () {
            // In a real app, use url_launcher to open the link
          },
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: const Color(0xFF3B82F6).withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      article.publisher.toUpperCase(),
                      style: const TextStyle(
                        color: Color(0xFF60A5FA),
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  const Spacer(),
                  Text(
                    _formatTime(article.published),
                    style: TextStyle(
                      color: const Color(0xFF94A3B8).withValues(alpha: 0.7),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                article.title,
                style: const TextStyle(
                  color: Color(0xFFE2E8F0),
                  fontSize: 15,
                  fontWeight: FontWeight.w500,
                  height: 1.4,
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  String _formatTime(String publishedTimestamp) {
    // Basic formatting. Real app should parse epoch or ISO.
    if (publishedTimestamp.contains('T')) {
      return publishedTimestamp.split('T').first;
    }
    return publishedTimestamp.length > 10
        ? publishedTimestamp.substring(0, 10)
        : publishedTimestamp;
  }
}
