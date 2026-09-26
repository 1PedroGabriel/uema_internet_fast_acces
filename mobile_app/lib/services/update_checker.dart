import 'dart:convert';
import 'package:http/http.dart' as http;

/// Resultado da verificação de atualização no GitHub Releases.
class UpdateInfo {
  final bool available;
  final String tag;
  final String url;
  final String notes;

  UpdateInfo({
    required this.available,
    required this.tag,
    required this.url,
    required this.notes,
  });
}

/// Verifica se há uma versão mais recente publicada no GitHub Releases.
/// Apenas leitura (GET na API pública); não baixa nem instala nada.
class UpdateChecker {
  static const String repo = '1PedroGabriel/uema_internet_fast_acces';
  static const String currentVersion = '1.0.0'; // sincronizar com pubspec.yaml

  static List<int> _parse(String tag) {
    final nums = RegExp(r'\d+').allMatches(tag).map((m) => int.parse(m.group(0)!)).toList();
    while (nums.length < 3) nums.add(0);
    return nums.sublist(0, 3);
  }

  static int _compare(List<int> a, List<int> b) {
    for (var i = 0; i < 3; i++) {
      if (a[i] != b[i]) return a[i].compareTo(b[i]);
    }
    return 0;
  }

  static Future<UpdateInfo?> check() async {
    try {
      final resp = await http.get(
        Uri.parse('https://api.github.com/repos/$repo/releases/latest'),
        headers: {
          'Accept': 'application/vnd.github+json',
          'User-Agent': 'UEMA-FastAccess-Mobile',
        },
      ).timeout(const Duration(seconds: 8));

      if (resp.statusCode != 200) return null;

      final data = jsonDecode(resp.body) as Map<String, dynamic>;
      final tag = (data['tag_name'] as String?) ?? '';
      final latest = _parse(tag);
      final current = _parse(currentVersion);

      final body = (data['body'] as String?) ?? '';

      return UpdateInfo(
        available: _compare(latest, current) > 0,
        tag: tag,
        url: (data['html_url'] as String?) ?? 'https://github.com/$repo/releases/latest',
        notes: body.length > 500 ? body.substring(0, 500) : body,
      );
    } catch (_) {
      return null;
    }
  }
}
