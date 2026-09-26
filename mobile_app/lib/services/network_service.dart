import 'package:http/http.dart' as http;

class NetworkService {
  // ==================================================================
  // ATENÇÃO DESENVOLVEDOR: ASSIM COMO NO DESKTOP, ALTERE AQUI A URL
  // E OS CAMPOS COM BASE NO QUE VOCÊ ACHAR NO "F12" (NETWORK) DA PÁGINA
  // ==================================================================
  static const String loginUrl = "https://SEU_PORTAL_DA_UEMA.br/login";
  static const String userField = "username";
  static const String passField = "password";

  static Future<bool> isCaptivePortal() async {
    try {
      // O Google possui esse endereço específico que só responde '204 No Content'
      // Se não retornar 204, significa que a rede da universidade sequestrou 
      // a requisição e a gente tá preso no portal.
      final response = await http.get(Uri.parse('http://clients3.google.com/generate_204'))
          .timeout(const Duration(seconds: 5));
      return response.statusCode != 204;
    } catch (e) {
      return true; // Se der erro de timeout, assume que a rede está bloqueada
    }
  }

  static Future<bool> doLogin(String username, String password) async {
    if (loginUrl.contains("SEU_PORTAL")) {
      print("ERRO: O desenvolvedor precisa configurar a URL no código fonte.");
      return false;
    }

    try {
      // Faz o POST seguro usando as credenciais do cofre
      final response = await http.post(
        Uri.parse(loginUrl),
        body: {
          userField: username,
          passField: password,
        },
      ).timeout(const Duration(seconds: 10));
      
      // Checa se a internet está liberada agora
      return !(await isCaptivePortal());
    } catch (e) {
      return false;
    }
  }
}
