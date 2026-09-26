import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorage {
  // Cria uma instância de armazenamento super segura:
  // Usa EncryptedSharedPreferences (Keystore) no Android e Keychain no iOS.
  static const _storage = FlutterSecureStorage();
  
  static const _keyUser = 'uema_username';
  static const _keyPass = 'uema_password';

  static Future<void> saveCredentials(String user, String pass) async {
    await _storage.write(key: _keyUser, value: user);
    await _storage.write(key: _keyPass, value: pass);
  }

  static Future<Map<String, String?>> getCredentials() async {
    String? user = await _storage.read(key: _keyUser);
    String? pass = await _storage.read(key: _keyPass);
    return {'user': user, 'pass': pass};
  }

  static Future<void> clear() async {
    await _storage.delete(key: _keyUser);
    await _storage.delete(key: _keyPass);
  }
}
