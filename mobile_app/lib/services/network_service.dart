import 'package:http/http.dart' as http;

class NetworkService {
  // Parâmetros oficiais do Captive Portal da UEMA (Extraídos do HTML original)
  static const String loginUrl = "http://172.25.50.10/auth/index.html/u";
  static const String userField = "user";
  static const String passField = "password";

  static Future<bool> isCaptivePortal() async {
    try {
      final response = await http.get(Uri.parse('http://clients3.google.com/generate_204'))
          .timeout(const Duration(seconds: 5));
      return response.statusCode != 204;
    } catch (e) {
      return true; 
    }
  }

  static Future<bool> doLogin(String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse(loginUrl),
        body: {
          userField: username,
          passField: password,
        },
      ).timeout(const Duration(seconds: 10));
      
      return !(await isCaptivePortal());
    } catch (e) {
      return false;
    }
  }
}
