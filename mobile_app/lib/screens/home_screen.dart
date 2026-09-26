import 'package:flutter/material.dart';
import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/secure_storage.dart';
import '../services/network_service.dart';
import '../services/update_checker.dart';
import '../services/foreground_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _userController = TextEditingController();
  final _passController = TextEditingController();

  static const Color _uemaBlue = Color(0xFF276489);

  bool _hasCredentials = false;
  bool _isLoading = false;
  bool _obscurePassword = true;
  String _statusMessage = '';
  UpdateInfo? _update;

  @override
  void initState() {
    super.initState();
    _checkSavedCredentials();
    _checkForUpdate();
    _requestPermissionsAndStartService();
  }

  /// Pede a permissão de notificação (Android 13+) e inicia o serviço de
  /// auto-login em primeiro plano se já houver credenciais salvas.
  Future<void> _requestPermissionsAndStartService() async {
    try {
      if (await FlutterForegroundTask.isIgnoringBatteryOptimizations == false) {
        // Não força: apenas se o usuário já tiver credenciais, o serviço inicia
      }
      final notif = await FlutterForegroundTask.checkNotificationPermission();
      if (notif != NotificationPermission.granted) {
        await FlutterForegroundTask.requestNotificationPermission();
      }
      final creds = await SecureStorage.getCredentials();
      if (creds['user'] != null && creds['pass'] != null) {
        await ForegroundServiceManager.start();
      }
    } catch (_) {}
  }

  Future<void> _checkForUpdate() async {
    final info = await UpdateChecker.check();
    if (!mounted || info == null) return;
    setState(() => _update = info);
  }

  Future<void> _checkSavedCredentials() async {
    final creds = await SecureStorage.getCredentials();
    if (!mounted) return;
    setState(() {
      _hasCredentials = creds['user'] != null && creds['pass'] != null;
      if (_hasCredentials) {
        _userController.text = creds['user']!;
      }
    });
    // Login automático ao abrir o app quando já há credenciais salvas
    if (_hasCredentials) {
      await _performLogin();
    }
  }

  Future<void> _saveAndLogin() async {
    final user = _userController.text.trim();
    final pass = _passController.text.trim();

    if (user.isEmpty || pass.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Por favor, informe seu usuário/matrícula e senha.'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    await SecureStorage.saveCredentials(user, pass);
    await ForegroundServiceManager.start();
    setState(() => _hasCredentials = true);
    await _performLogin();
  }

  Future<void> _performLogin() async {
    setState(() {
      _isLoading = true;
      _statusMessage = 'Testando conexão com a rede...';
    });

    // 1. Testa conectividade real
    final status = await NetworkService.checkStatus();
    if (!mounted) return;

    if (status == PortalStatus.online) {
      setState(() {
        _statusMessage = 'A internet já está liberada e funcionando!';
        _isLoading = false;
      });
      return;
    }

    if (status == PortalStatus.offline) {
      setState(() {
        _statusMessage =
            'Sem conexão. Verifique se o Wi-Fi UEMA está conectado.';
        _isLoading = false;
      });
      return;
    }

    setState(() => _statusMessage = 'Portal cativo detectado. Autenticando...');

    final creds = await SecureStorage.getCredentials();
    if (!mounted) return;
    if (creds['user'] == null || creds['pass'] == null) {
      setState(() {
        _hasCredentials = false;
        _isLoading = false;
        _statusMessage = 'Credenciais não encontradas. Configure novamente.';
      });
      return;
    }

    bool success = await NetworkService.doLogin(creds['user']!, creds['pass']!);
    if (!mounted) return;

    setState(() {
      _isLoading = false;
      _statusMessage = success
          ? 'Conectado com sucesso à rede UEMA!'
          : 'Falha no login. Verifique sua senha do SIGUEMA ou se está na rede UEMA.';
    });
  }

  Future<void> _confirmClearCredentials() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Remover Credenciais?'),
        content: const Text('Você terá que digitar seu login e senha novamente no próximo acesso.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Remover'),
          ),
        ],
      ),
    );

    if (confirm == true) {
      await SecureStorage.clear();
      await ForegroundServiceManager.stop();
      setState(() {
        _hasCredentials = false;
        _userController.clear();
        _passController.clear();
        _statusMessage = 'Credenciais removidas com segurança.';
      });
    }
  }

  @override
  void dispose() {
    _userController.dispose();
    _passController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('UEMA Wi-Fi Fast', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          if (_hasCredentials)
            IconButton(
              icon: const Icon(Icons.logout),
              onPressed: _confirmClearCredentials,
              tooltip: 'Trocar Usuário',
            )
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (_update != null && _update!.available)
                Container(
                  margin: const EdgeInsets.only(bottom: 20),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFFe8f4fd),
                    border: Border.all(color: _uemaBlue),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.system_update, color: _uemaBlue),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          'Versão ${_update!.tag} disponível. Toque para baixar e ver as melhorias de segurança.',
                          style: const TextStyle(fontSize: 13, color: _uemaBlue, fontWeight: FontWeight.w600),
                        ),
                      ),
                      TextButton(
                        onPressed: () => launchUrl(Uri.parse(_update!.url)),
                        child: const Text('Abrir'),
                      ),
                    ],
                  ),
                ),
              const SizedBox(height: 20),
              const Icon(Icons.wifi_lock, size: 75, color: _uemaBlue),
              const SizedBox(height: 20),
              
              if (!_hasCredentials) ...[
                const Text(
                  'Configuração Inicial',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Suas credenciais serão salvas de forma criptografada no cofre de hardware do seu aparelho.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.grey, fontSize: 13),
                ),
                const SizedBox(height: 25),
                TextField(
                  controller: _userController,
                  decoration: const InputDecoration(
                    labelText: 'Usuário / Matrícula SIGUEMA',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.person),
                  ),
                ),
                const SizedBox(height: 15),
                TextField(
                  controller: _passController,
                  obscureText: _obscurePassword,
                  decoration: InputDecoration(
                    labelText: 'Senha SIGUEMA',
                    border: const OutlineInputBorder(),
                    prefixIcon: const Icon(Icons.lock),
                    suffixIcon: IconButton(
                      icon: Icon(_obscurePassword
                          ? Icons.visibility
                          : Icons.visibility_off),
                      tooltip: _obscurePassword ? 'Mostrar senha' : 'Ocultar senha',
                      onPressed: () =>
                          setState(() => _obscurePassword = !_obscurePassword),
                    ),
                  ),
                ),
                const SizedBox(height: 25),
                ElevatedButton(
                  onPressed: _saveAndLogin,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    backgroundColor: _uemaBlue,
                    foregroundColor: Colors.white,
                  ),
                  child: const Text('Salvar e Conectar', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                ),
              ] else ...[
                Card(
                  elevation: 3,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  child: Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.check_circle, color: _uemaBlue, size: 20),
                            const SizedBox(width: 8),
                            Text(
                              'Matrícula: ${_userController.text}',
                              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                            ),
                          ],
                        ),
                        const SizedBox(height: 25),
                        ElevatedButton.icon(
                          onPressed: _isLoading ? null : _performLogin,
                          icon: _isLoading 
                              ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                              : const Icon(Icons.bolt, color: Colors.white, size: 28),
                          label: const Text('1-Tap Connect', style: TextStyle(fontSize: 20, color: Colors.white, fontWeight: FontWeight.bold)),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: _uemaBlue,
                            padding: const EdgeInsets.symmetric(vertical: 18),
                            minimumSize: const Size(double.infinity, 64),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 25),
                if (_statusMessage.isNotEmpty)
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade100,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.grey.shade300),
                    ),
                    child: Text(
                      _statusMessage, 
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.blueGrey),
                    ),
                  ),
              ]
            ],
          ),
        ),
      ),
    );
  }
}
