import 'package:flutter/material.dart';
import '../services/secure_storage.dart';
import '../services/network_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _userController = TextEditingController();
  final _passController = TextEditingController();
  
  bool _hasCredentials = false;
  bool _isLoading = false;
  String _statusMessage = '';

  @override
  void initState() {
    super.initState();
    _checkSavedCredentials();
  }

  Future<void> _checkSavedCredentials() async {
    final creds = await SecureStorage.getCredentials();
    setState(() {
      _hasCredentials = creds['user'] != null && creds['pass'] != null;
      if (_hasCredentials) {
        _userController.text = creds['user']!;
      }
    });
  }

  Future<void> _saveAndLogin() async {
    if (_userController.text.isEmpty || _passController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Por favor, preencha usuário e senha!')),
      );
      return;
    }

    await SecureStorage.saveCredentials(_userController.text, _passController.text);
    setState(() => _hasCredentials = true);
    await _performLogin();
  }

  Future<void> _performLogin() async {
    setState(() {
      _isLoading = true;
      _statusMessage = 'Checando rede...';
    });

    bool isPortal = await NetworkService.isCaptivePortal();
    
    if (!isPortal) {
      setState(() {
        _statusMessage = 'A internet já está liberada!';
        _isLoading = false;
      });
      return;
    }

    setState(() => _statusMessage = 'Autenticando...');
    
    final creds = await SecureStorage.getCredentials();
    bool success = await NetworkService.doLogin(creds['user']!, creds['pass']!);

    setState(() {
      _isLoading = false;
      _statusMessage = success 
          ? 'Conectado com sucesso na rede UEMA!' 
          : 'Falha no login. Verifique sua senha ou se está na rede correta.';
    });
  }

  Future<void> _clearCredentials() async {
    await SecureStorage.clear();
    setState(() {
      _hasCredentials = false;
      _userController.clear();
      _passController.clear();
      _statusMessage = '';
    });
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
              onPressed: _clearCredentials,
              tooltip: 'Trocar Usuário',
            )
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Icon(Icons.wifi_lock, size: 80, color: Colors.green),
            const SizedBox(height: 30),
            
            if (!_hasCredentials) ...[
              const Text(
                'Configure seu acesso',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 10),
              const Text(
                'Suas informações serão salvas com criptografia no cofre nativo do seu aparelho.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey),
              ),
              const SizedBox(height: 30),
              TextField(
                controller: _userController,
                decoration: const InputDecoration(
                  labelText: 'Usuário/Matrícula',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.person),
                ),
              ),
              const SizedBox(height: 15),
              TextField(
                controller: _passController,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'Senha',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.lock),
                ),
              ),
              const SizedBox(height: 25),
              ElevatedButton(
                onPressed: _saveAndLogin,
                style: ElevatedButton.styleFrom(padding: const EdgeInsets.all(16)),
                child: const Text('Salvar e Conectar', style: TextStyle(fontSize: 18)),
              ),
            ] else ...[
              Card(
                elevation: 4,
                child: Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: Column(
                    children: [
                      Text('Usuário Salvo: ${_userController.text}', style: const TextStyle(fontSize: 16)),
                      const SizedBox(height: 30),
                      ElevatedButton.icon(
                        onPressed: _isLoading ? null : _performLogin,
                        icon: _isLoading 
                            ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                            : const Icon(Icons.bolt, color: Colors.white),
                        label: const Text('1-Tap Connect', style: TextStyle(fontSize: 20, color: Colors.white)),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.green,
                          padding: const EdgeInsets.symmetric(vertical: 20),
                          minimumSize: const Size(double.infinity, 60),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 30),
              Text(
                _statusMessage, 
                textAlign: TextAlign.center,
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.blueGrey),
              ),
            ]
          ],
        ),
      ),
    );
  }
}
