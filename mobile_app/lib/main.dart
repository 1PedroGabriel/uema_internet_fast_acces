import 'package:flutter/material.dart';
import 'screens/home_screen.dart';
import 'services/foreground_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  ForegroundServiceManager.init();
  runApp(const UemaFastAccessApp());
}

class UemaFastAccessApp extends StatelessWidget {
  const UemaFastAccessApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'UEMA Wi-Fi Fast',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF276489)),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}
