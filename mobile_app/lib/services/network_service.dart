import 'dart:io';
import 'package:http/http.dart' as http;

/// Resultado da verificação de conectividade.
/// Distingue "sem rede" de "portal cativo" para não disparar logins inúteis offline.
enum PortalStatus { online, captivePortal, offline }

class NetworkService {
  // Fallback: endereço do Captive Portal observado no campus. O endereço real
  // é descoberto dinamicamente a cada conexão (ver _discoverPortalUrl), pois
  // pode variar entre campi/controladores.
  static const String loginUrl = "http://172.25.50.10/auth/index.html/u";
  static const String probeUrl = "http://www.msftconnecttest.com/connecttest.txt";
  static const String userField = "user";
  static const String passField = "password";

  /// True se o IP pertence às faixas privadas/locais (RFC1918, loopback).
  static bool _isPrivateIp(String ip) {
    if (ip.startsWith('10.') ||
        ip.startsWith('192.168.') ||
        ip.startsWith('127.')) {
      return true;
    }
    if (ip.startsWith('172.')) {
      final second = int.tryParse(ip.split('.')[1]) ?? -1;
      return second >= 16 && second <= 31;
    }
    return false;
  }

  /// Mitigação anti-vazamento de credenciais:
  /// só envia a senha se o aparelho estiver em uma rede privada.
  /// IMPORTANTE: o IP do cliente na rede UEMA pode ser 10.x.x.x (observado
  /// 10.101.x.x) enquanto o controlador usa 172.25.x.x — por isso qualquer
  /// faixa privada é aceita aqui, e a URL do portal é validada em doLogin().
  static Future<bool> _isOnPrivateNetwork() async {
    try {
      final interfaces =
          await NetworkInterface.list(type: InternetAddressType.IPv4);
      for (final interface in interfaces) {
        for (final addr in interface.addresses) {
          if (_isPrivateIp(addr.address)) return true;
        }
      }
    } catch (_) {}
    return false;
  }

  /// Descobre dinamicamente a URL de autenticação do portal: segue o
  /// redirecionamento do probe e extrai o 'action' do formulário.
  /// Só aceita destino HTTP em IP privado (anti-phishing).
  static Future<Uri> _discoverPortalUrl() async {
    try {
      final probeResp = await http
          .get(Uri.parse(probeUrl))
          .timeout(const Duration(seconds: 4));

      if (probeResp.statusCode == 200 &&
          probeResp.body.contains("Microsoft Connect Test")) {
        return Uri.parse(loginUrl); // Internet livre; fallback irrelevante
      }

      final formMatch = RegExp(
        '<form[^>]*action=["\x27]([^"\x27]+)["\x27]',
        caseSensitive: false,
      ).firstMatch(probeResp.body);
      if (formMatch == null) return Uri.parse(loginUrl);

      final base = probeResp.request?.url ?? Uri.parse(probeUrl);
      final discovered = base.resolve(formMatch.group(1)!);
      if (discovered.scheme == 'http' && _isPrivateIp(discovered.host)) {
        return discovered;
      }
    } catch (_) {}
    return Uri.parse(loginUrl); // Fallback fixo (IP privado conhecido)
  }

  static Future<PortalStatus> checkStatus() async {
    try {
      final response = await http
          .get(Uri.parse(probeUrl))
          .timeout(const Duration(seconds: 4));

      // 200 com a string de teste: internet livre
      if (response.statusCode == 200 &&
          response.body.contains("Microsoft Connect Test")) {
        return PortalStatus.online;
      }
      // Resposta HTTP diferente do esperado: provável interceptação do portal
      return PortalStatus.captivePortal;
    } catch (_) {
      // Exceção (timeout/DNS): sem conectividade, não dá para afirmar portal
      return PortalStatus.offline;
    }
  }

  static Future<bool> doLogin(String username, String password) async {
    // Nunca envia a senha fora de uma rede privada
    if (!await _isOnPrivateNetwork()) return false;

    try {
      // 1. Descobre a URL real do portal (handshake + parsing do formulário)
      final target = await _discoverPortalUrl();

      // 2. Disparo do POST com cabeçalho Referer para evitar bloqueio 403
      await http.post(
        target,
        headers: {
          'Referer': target.toString(),
          'User-Agent': 'Mozilla/5.0 (Mobile; UEMA-FastAccess)',
        },
        body: {
          userField: username,
          passField: password,
        },
      ).timeout(const Duration(seconds: 8));

      // 3. Aguarda 2 segundos para o firewall da UEMA aplicar o desbloqueio
      await Future.delayed(const Duration(seconds: 2));

      return (await checkStatus()) == PortalStatus.online;
    } catch (e) {
      return false;
    }
  }
}
