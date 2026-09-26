import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
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
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}
