import 'package:http/http.dart' as http;

class NetworkService {
  // Parâmetros oficiais do Captive Portal da UEMA
  static const String loginUrl = "http://172.25.50.10/auth/index.html/u";
  static const String probeUrl = "http://www.msftconnecttest.com/connecttest.txt";
  static const String userField = "user";
  static const String passField = "password";

  static Future<bool> isCaptivePortal() async {
    try {
      final response = await http.get(Uri.parse(probeUrl))
          .timeout(const Duration(seconds: 4));
      
      // Se retornar 200 com a string de teste, internet está livre
      if (response.statusCode == 200 && response.body.contains("Microsoft Connect Test")) {
        return false;
      }
      return true;
    } catch (e) {
      return true; 
    }
  }

  static Future<bool> doLogin(String username, String password) async {
    try {
      // 1. Handshake inicial para obter cookies e iniciar sessão no portal
      try {
        await http.get(Uri.parse(probeUrl)).timeout(const Duration(seconds: 4));
      } catch (_) {}

      // 2. Disparo do POST com cabeçalho Referer para evitar bloqueio 403
      await http.post(
        Uri.parse(loginUrl),
        headers: {
          'Referer': loginUrl,
          'User-Agent': 'Mozilla/5.0 (Mobile; UEMA-FastAccess)',
        },
        body: {
          userField: username,
          passField: password,
        },
      ).timeout(const Duration(seconds: 8));

      // 3. Aguarda 2 segundos para o firewall da UEMA aplicar o desbloqueio
      await Future.delayed(const Duration(seconds: 2));

      return !(await isCaptivePortal());
    } catch (e) {
      return false;
    }
  }
}
