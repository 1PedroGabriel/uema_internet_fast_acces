import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:network_info_plus/network_info_plus.dart';
import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'secure_storage.dart';
import 'network_service.dart';

/// Manipulador do serviço em primeiro plano.
///
/// Roda num isolate separado enquanto o Android mantém o serviço vivo
/// (notificação permanente obrigatória do sistema). A cada minuto verifica
/// a conectividade; ao detectar o portal cativo da UEMA, autentica
/// automaticamente com as credenciais salvas — sem o usuário abrir o app.
class UemaTaskHandler extends TaskHandler {
  int _failureCount = 0;
  DateTime _lastAttempt = DateTime.fromMillisecondsSinceEpoch(0);
  StreamSubscription<List<ConnectivityResult>>? _connectivitySub;
  bool _checking = false;

  @override
  Future<void> onStart(DateTime timestamp, TaskStarter starter) async {
    // Reage INSTANTANEAMENTE quando a rede muda (Wi-Fi conectou/trocou)
    // em vez de esperar o próximo ciclo do timer. Esse é o "próprio negócio
    // de wifi" do Android: callback nativo de conectividade.
    _connectivitySub = Connectivity()
        .onConnectivityChanged
        .listen((_) => _onNetworkChanged());
  }

  Future<void> _onNetworkChanged() async {
    // Só age se a nova rede for Wi-Fi com SSID UEMA
    try {
      final ssid = await NetworkInfo().getWifiName();
      if (ssid != null && ssid.replaceAll('"', '').toUpperCase() == 'UEMA') {
        await _checkAndLogin();
      }
    } catch (_) {}
  }

  @override
  void onRepeatEvent(DateTime timestamp) {
    // Timer de segurança a cada 60s caso o callback de conectividade falhe
    _checkAndLogin();
  }

  Future<void> _checkAndLogin() async {
    if (_checking) return; // evita execuções concorrentes timer+callback
    _checking = true;
    try {
      await _doCheck();
    } finally {
      _checking = false;
    }
  }

  Future<void> _doCheck() async {
    final status = await NetworkService.checkStatus();

    if (status == PortalStatus.online) {
      _failureCount = 0;
      await FlutterForegroundTask.updateService(
        notificationTitle: 'FastAccess',
        notificationText: 'Conectado à rede UEMA',
      );
      return;
    }

    if (status == PortalStatus.offline) {
      await FlutterForegroundTask.updateService(
        notificationTitle: 'FastAccess',
        notificationText: 'Aguardando a rede UEMA...',
      );
      return;
    }

    // Portal cativo detectado: autentica com circuit breaker (5 falhas -> 10 min)
    if (_failureCount >= 5) {
      final cooldown = DateTime.now().difference(_lastAttempt).inMinutes;
      if (cooldown < 10) {
        await FlutterForegroundTask.updateService(
          notificationTitle: 'FastAccess',
          notificationText: 'Senha rejeitada? Abra o app para atualizar.',
        );
        return;
      }
      _failureCount = 0;
    }

    final creds = await SecureStorage.getCredentials();
    if (creds['user'] == null || creds['pass'] == null) {
      await FlutterForegroundTask.updateService(
        notificationTitle: 'FastAccess',
        notificationText: 'Toque para cadastrar suas credenciais',
      );
      return;
    }

    _lastAttempt = DateTime.now();
    final success = await NetworkService.doLogin(creds['user']!, creds['pass']!);
    if (success) {
      _failureCount = 0;
      await FlutterForegroundTask.updateService(
        notificationTitle: 'FastAccess',
        notificationText: 'Autenticado automaticamente!',
      );
    } else {
      _failureCount++;
      await FlutterForegroundTask.updateService(
        notificationTitle: 'FastAccess',
        notificationText: 'Tentando autenticar... ($_failureCount/5)',
      );
    }
  }

  @override
  Future<void> onDestroy(DateTime timestamp, bool isTimeout) async {
    await _connectivitySub?.cancel();
  }
}

/// Inicialização e controle do serviço de auto-login.
class ForegroundServiceManager {
  static void init() {
    FlutterForegroundTask.init(
      androidNotificationOptions: AndroidNotificationOptions(
        channelId: 'uema_fastaccess_service',
        channelName: 'Auto-login UEMA',
        channelDescription:
            'Mantém a verificação da rede UEMA ativa para conectar automaticamente.',
        channelImportance: NotificationChannelImportance.LOW,
        priority: NotificationPriority.LOW,
      ),
      iosNotificationOptions: const IOSNotificationOptions(
        showNotification: false,
      ),
      foregroundTaskOptions: ForegroundTaskOptions(
        eventAction: ForegroundTaskEventAction.repeat(60000), // 1 minuto
        autoRunOnBoot: true,
        autoRunOnMyPackageReplaced: true,
        allowWakeLock: true,
        allowWifiLock: true,
      ),
    );
  }

  /// Inicia o serviço (chamado após salvar credenciais ou ao abrir o app).
  static Future<void> start() async {
    if (await FlutterForegroundTask.isRunningService) return;
    await FlutterForegroundTask.startService(
      serviceId: 256,
      notificationTitle: 'FastAccess',
      notificationText: 'Monitorando a rede UEMA...',
      callback: _startCallback,
    );
  }

  static Future<void> stop() async {
    if (await FlutterForegroundTask.isRunningService) {
      await FlutterForegroundTask.stopService();
    }
  }
}

@pragma('vm:entry-point')
void _startCallback() {
  FlutterForegroundTask.setTaskHandler(UemaTaskHandler());
}
