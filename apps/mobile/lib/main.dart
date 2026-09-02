import 'dart:convert';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

const apiBaseUrl = String.fromEnvironment('NOVA_API_URL', defaultValue: 'http://10.0.2.2:8000');

void main() => runApp(const NovaApp());

class NovaApp extends StatelessWidget {
  const NovaApp({super.key});

  @override
  Widget build(BuildContext context) {
    final scheme = ColorScheme.fromSeed(seedColor: const Color(0xFF7C4DFF), brightness: Brightness.dark);
    return MaterialApp(
      title: 'NOVA AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(useMaterial3: true, colorScheme: scheme, scaffoldBackgroundColor: const Color(0xFF090A12), cardTheme: const CardThemeData(color: Color(0xFF141522))),
      home: const EntryScreen(),
    );
  }
}

class NovaApi {
  static final _client = http.Client();
  static String? token;

  static Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };

  static Future<bool> login(String username, String password) async {
    final response = await _client.post(Uri.parse('$apiBaseUrl/v1/auth/login'), headers: {'Content-Type': 'application/json'}, body: jsonEncode({'username': username, 'password': password}));
    if (response.statusCode >= 300) return false;
    token = (jsonDecode(response.body) as Map<String, dynamic>)['access_token'] as String;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('nova_token', token!);
    return true;
  }

  static Future<void> restore() async {
    final prefs = await SharedPreferences.getInstance();
    token = prefs.getString('nova_token');
  }

  static Future<void> logout() async {
    token = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('nova_token');
  }

  static Future<Map<String, dynamic>> chat(String message, {bool rag = true}) async {
    final response = await _client.post(Uri.parse('$apiBaseUrl/v1/chat'), headers: _headers, body: jsonEncode({'message': message, 'use_rag': rag}));
    if (response.statusCode == 401) throw const ApiException('Session expired. Please sign in again.');
    if (response.statusCode >= 300) throw ApiException(response.body);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }
}

class ApiException implements Exception {
  final String message;
  const ApiException(this.message);
  @override
  String toString() => message;
}

class EntryScreen extends StatefulWidget {
  const EntryScreen({super.key});
  @override
  State<EntryScreen> createState() => _EntryScreenState();
}

class _EntryScreenState extends State<EntryScreen> {
  bool loading = true;
  @override
  void initState() {
    super.initState();
    _restore();
  }
  Future<void> _restore() async {
    await NovaApi.restore();
    if (!mounted) return;
    setState(() => loading = false);
  }
  @override
  Widget build(BuildContext context) {
    if (loading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    return NovaApi.token == null ? const LoginScreen() : const NovaShell();
  }
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final username = TextEditingController(text: 'admin');
  final password = TextEditingController();
  bool busy = false;
  bool obscure = true;
  String? error;

  Future<void> _login() async {
    if (username.text.trim().isEmpty || password.text.isEmpty) return;
    setState(() { busy = true; error = null; });
    try {
      if (await NovaApi.login(username.text.trim(), password.text)) {
        if (mounted) Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => const NovaShell()));
      } else {
        setState(() => error = 'Invalid NOVA credentials');
      }
    } catch (e) {
      setState(() => error = 'Unable to connect to NOVA API');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: Container(
          decoration: const BoxDecoration(gradient: LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight, colors: [Color(0xFF17132C), Color(0xFF090A12), Color(0xFF101827)])),
          child: SafeArea(
            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(28),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 440),
                  child: Column(children: [
                    Container(width: 92, height: 92, decoration: BoxDecoration(borderRadius: BorderRadius.circular(28), gradient: const LinearGradient(colors: [Color(0xFF9C6CFF), Color(0xFF4DD0E1)]), boxShadow: const [BoxShadow(blurRadius: 32, spreadRadius: 2)]), child: const Icon(Icons.auto_awesome_rounded, size: 48, color: Colors.white)),
                    const SizedBox(height: 24),
                    const Text('NOVA', style: TextStyle(fontSize: 40, fontWeight: FontWeight.w800, letterSpacing: 5)),
                    const SizedBox(height: 6),
                    Text('Your private, self-hosted AI', style: TextStyle(color: Colors.white.withValues(alpha: .65), fontSize: 16)),
                    const SizedBox(height: 42),
                    Card(child: Padding(padding: const EdgeInsets.all(22), child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                      const Text('Welcome back', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 6),
                      Text('Sign in to chat with your NOVA model.', style: TextStyle(color: Colors.white.withValues(alpha: .6))),
                      const SizedBox(height: 22),
                      TextField(controller: username, textInputAction: TextInputAction.next, decoration: const InputDecoration(labelText: 'Username', prefixIcon: Icon(Icons.person_outline), border: OutlineInputBorder())),
                      const SizedBox(height: 14),
                      TextField(controller: password, obscureText: obscure, onSubmitted: (_) => _login(), decoration: InputDecoration(labelText: 'Password', prefixIcon: const Icon(Icons.lock_outline), border: const OutlineInputBorder(), suffixIcon: IconButton(onPressed: () => setState(() => obscure = !obscure), icon: Icon(obscure ? Icons.visibility : Icons.visibility_off)))),
                      if (error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(error!, style: TextStyle(color: Theme.of(context).colorScheme.error))),
                      const SizedBox(height: 20),
                      FilledButton.icon(onPressed: busy ? null : _login, icon: busy ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.login_rounded), label: Text(busy ? 'Signing in...' : 'Sign in'), style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 15))),
                    ]))),
                    const SizedBox(height: 18),
                    Row(mainAxisAlignment: MainAxisAlignment.center, children: [const Icon(Icons.shield_outlined, size: 16), const SizedBox(width: 6), Text('Self-hosted • Private • No hosted AI provider', style: TextStyle(fontSize: 12, color: Colors.white54))]),
                  ]),
                ),
              ),
            ),
          ),
        ),
      );
}

class NovaShell extends StatefulWidget {
  const NovaShell({super.key});
  @override
  State<NovaShell> createState() => _NovaShellState();
}

class _NovaShellState extends State<NovaShell> {
  int index = 0;
  final pages = const [ChatScreen(), TrainingScreen()];
  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: Row(children: [Container(width: 34, height: 34, decoration: BoxDecoration(borderRadius: BorderRadius.circular(10), gradient: const LinearGradient(colors: [Color(0xFF9C6CFF), Color(0xFF4DD0E1)])), child: const Icon(Icons.auto_awesome, size: 19)), const SizedBox(width: 10), const Text('NOVA', style: TextStyle(fontWeight: FontWeight.w800, letterSpacing: 2))]),
          actions: [IconButton(tooltip: 'Sign out', onPressed: () async { await NovaApi.logout(); if (context.mounted) Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => const LoginScreen())); }, icon: const Icon(Icons.logout_rounded))],
        ),
        body: pages[index],
        bottomNavigationBar: NavigationBar(selectedIndex: index, onDestinationSelected: (value) => setState(() => index = value), destinations: const [NavigationDestination(icon: Icon(Icons.chat_bubble_outline), selectedIcon: Icon(Icons.chat_bubble), label: 'Chat'), NavigationDestination(icon: Icon(Icons.model_training_outlined), selectedIcon: Icon(Icons.model_training), label: 'Train')]),
      );
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});
  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final input = TextEditingController();
  final scroll = ScrollController();
  final messages = <Map<String, dynamic>>[];
  bool busy = false;
  bool rag = true;

  Future<void> send() async {
    final text = input.text.trim();
    if (text.isEmpty || busy) return;
    setState(() { busy = true; messages.add({'role': 'user', 'text': text}); input.clear(); });
    _scrollDown();
    try {
      final data = await NovaApi.chat(text, rag: rag);
      setState(() => messages.add({'role': 'assistant', 'text': '${data['text']}', 'rag': data['metadata']?['rag_used'] == true}));
    } catch (e) {
      setState(() => messages.add({'role': 'assistant', 'text': 'NOVA connection error: $e'}));
    } finally { if (mounted) { setState(() => busy = false); _scrollDown(); } }
  }
  void _scrollDown() { WidgetsBinding.instance.addPostFrameCallback((_) { if (scroll.hasClients) scroll.animateTo(scroll.position.maxScrollExtent, duration: const Duration(milliseconds: 250), curve: Curves.easeOut); }); }
  @override
  Widget build(BuildContext context) => Column(children: [
        Expanded(child: messages.isEmpty ? _Welcome() : ListView.builder(controller: scroll, padding: const EdgeInsets.fromLTRB(16, 16, 16, 12), itemCount: messages.length, itemBuilder: (_, i) { final item = messages[i]; final user = item['role'] == 'user'; return _Bubble(text: item['text'] as String, user: user, rag: item['rag'] == true); })),
        SafeArea(child: Padding(padding: const EdgeInsets.fromLTRB(12, 4, 12, 10), child: Column(children: [Row(children: [FilterChip(selected: rag, onSelected: (v) => setState(() => rag = v), avatar: const Icon(Icons.menu_book_outlined, size: 17), label: const Text('Knowledge / RAG')), const Spacer(), if (busy) const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))]), const SizedBox(height: 8), Row(crossAxisAlignment: CrossAxisAlignment.end, children: [Expanded(child: TextField(controller: input, minLines: 1, maxLines: 5, textInputAction: TextInputAction.newline, decoration: InputDecoration(hintText: 'Ask NOVA anything...', filled: true, fillColor: const Color(0xFF141522), border: OutlineInputBorder(borderRadius: BorderRadius.circular(20), borderSide: BorderSide.none), contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 13)))), const SizedBox(width: 8), IconButton.filled(onPressed: busy ? null : send, icon: const Icon(Icons.arrow_upward_rounded), style: IconButton.styleFrom(padding: const EdgeInsets.all(15)))]))]))),
      ]);
}

class _Welcome extends StatelessWidget {
  @override
  Widget build(BuildContext context) => Center(child: Padding(padding: const EdgeInsets.all(28), child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [Icon(Icons.auto_awesome_rounded, size: 58, color: Theme.of(context).colorScheme.primary), const SizedBox(height: 16), const Text('Hello, I’m NOVA', style: TextStyle(fontSize: 29, fontWeight: FontWeight.bold)), const SizedBox(height: 8), const Text('Chat with your local model. Enable Knowledge / RAG to ground answers with your private vector database.', textAlign: TextAlign.center, style: TextStyle(color: Colors.white60, height: 1.5)), const SizedBox(height: 24), Wrap(spacing: 8, runSpacing: 8, alignment: WrapAlignment.center, children: const [Chip(label: Text('Ask a question')), Chip(label: Text('Summarize')), Chip(label: Text('Write code'))])])));
}

class _Bubble extends StatelessWidget {
  final String text;
  final bool user;
  final bool rag;
  const _Bubble({required this.text, required this.user, required this.rag});
  @override
  Widget build(BuildContext context) => Align(alignment: user ? Alignment.centerRight : Alignment.centerLeft, child: Container(constraints: const BoxConstraints(maxWidth: 360), margin: const EdgeInsets.only(bottom: 12), padding: const EdgeInsets.all(15), decoration: BoxDecoration(borderRadius: BorderRadius.only(topLeft: const Radius.circular(18), topRight: const Radius.circular(18), bottomLeft: Radius.circular(user ? 18 : 4), bottomRight: Radius.circular(user ? 4 : 18)), gradient: user ? const LinearGradient(colors: [Color(0xFF6C43D9), Color(0xFF4D73E6)]) : null, color: user ? null : const Color(0xFF151724)), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(text, style: const TextStyle(fontSize: 15.5, height: 1.45)), if (!user && rag) const Padding(padding: EdgeInsets.only(top: 8), child: Row(children: [Icon(Icons.auto_awesome, size: 13), SizedBox(width: 4), Text('Grounded with private knowledge', style: TextStyle(fontSize: 11, color: Colors.white54))]))]));
}

class TrainingScreen extends StatefulWidget {
  const TrainingScreen({super.key});
  @override
  State<TrainingScreen> createState() => _TrainingScreenState();
}

class _TrainingScreenState extends State<TrainingScreen> {
  String status = 'Ready to train';
  bool busy = false;

  Future<void> upload() async {
    final result = await FilePicker.platform.pickFiles(withData: true, type: FileType.custom, allowedExtensions: ['csv', 'xlsx', 'md']);
    if (result == null) return;
    final file = result.files.single;
    if (file.bytes == null) return;
    setState(() { busy = true; status = 'Uploading ${file.name}...'; });
    try {
      final request = http.MultipartRequest('POST', Uri.parse('$apiBaseUrl/v1/datasets/upload'));
      request.headers['Authorization'] = 'Bearer ${NovaApi.token}';
      request.files.add(http.MultipartFile.fromBytes('file', file.bytes!, filename: file.name));
      final response = await request.send();
      if (response.statusCode >= 300) throw ApiException(await response.stream.bytesToString());
      setState(() => status = 'Uploaded ${file.name}');
    } catch (e) { setState(() => status = 'Upload failed: $e'); } finally { setState(() => busy = false); }
  }

  Future<void> prepare() async {
    setState(() { busy = true; status = 'Preparing JSONL dataset...'; });
    try {
      final response = await http.post(Uri.parse('$apiBaseUrl/v1/datasets/prepare'), headers: {'Authorization': 'Bearer ${NovaApi.token}'});
      if (response.statusCode >= 300) throw ApiException(response.body);
      final data = jsonDecode(response.body);
      setState(() => status = 'Prepared ${data['records']} training records');
    } catch (e) { setState(() => status = 'Preparation failed: $e'); } finally { setState(() => busy = false); }
  }

  Future<void> train() async {
    setState(() { busy = true; status = 'Starting NOVA training job...'; });
    try {
      final response = await http.post(Uri.parse('$apiBaseUrl/v1/train'), headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer ${NovaApi.token}'}, body: jsonEncode({}));
      if (response.statusCode >= 300) throw ApiException(response.body);
      final data = jsonDecode(response.body);
      setState(() => status = 'Training started • job PID ${data['pid'] ?? 'server'}');
    } catch (e) { setState(() => status = 'Training could not start: $e'); } finally { setState(() => busy = false); }
  }

  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.fromLTRB(16, 16, 16, 30), children: [
        Container(padding: const EdgeInsets.all(20), decoration: BoxDecoration(borderRadius: BorderRadius.circular(24), gradient: const LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight, colors: [Color(0xFF24184A), Color(0xFF122638)])), child: const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Icon(Icons.model_training_rounded, size: 34), SizedBox(height: 12), Text('Teach NOVA', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold)), SizedBox(height: 6), Text('Upload knowledge, prepare your dataset, then launch a self-hosted LoRA training job.', style: TextStyle(color: Colors.white70, height: 1.4))])),
        const SizedBox(height: 18),
        _StepCard(number: '01', icon: Icons.upload_file_rounded, title: 'Upload training data', subtitle: 'CSV, Excel or Markdown', child: FilledButton.icon(onPressed: busy ? null : upload, icon: const Icon(Icons.add), label: const Text('Choose file'))),
        _StepCard(number: '02', icon: Icons.dataset_rounded, title: 'Prepare dataset', subtitle: 'Normalize files into conversational JSONL', child: OutlinedButton.icon(onPressed: busy ? null : prepare, icon: const Icon(Icons.auto_fix_high), label: const Text('Prepare JSONL'))),
        _StepCard(number: '03', icon: Icons.rocket_launch_rounded, title: 'Train NOVA', subtitle: 'Run LoRA fine-tuning on your own GPU server', child: FilledButton.icon(onPressed: busy ? null : train, icon: const Icon(Icons.play_arrow_rounded), label: const Text('Start training'))),
        const SizedBox(height: 8),
        Card(child: Padding(padding: const EdgeInsets.all(16), child: Row(children: [const Icon(Icons.info_outline), const SizedBox(width: 12), Expanded(child: Text(status, style: const TextStyle(height: 1.35)))]))),
        const SizedBox(height: 10),
        const Text('Training changes model weights only after the training job completes. Ollama is the inference runtime; it does not replace the training worker.', style: TextStyle(color: Colors.white54, fontSize: 12, height: 1.4)),
      ]);
}

class _StepCard extends StatelessWidget {
  final String number;
  final IconData icon;
  final String title;
  final String subtitle;
  final Widget child;
  const _StepCard({required this.number, required this.icon, required this.title, required this.subtitle, required this.child});
  @override
  Widget build(BuildContext context) => Card(margin: const EdgeInsets.only(bottom: 12), child: Padding(padding: const EdgeInsets.all(16), child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Container(width: 44, height: 44, decoration: BoxDecoration(borderRadius: BorderRadius.circular(14), color: Theme.of(context).colorScheme.primary.withValues(alpha: .16)), child: Center(child: Icon(icon))), const SizedBox(width: 14), Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text('$number  $title', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)), const SizedBox(height: 4), Text(subtitle, style: const TextStyle(color: Colors.white54, fontSize: 13)), const SizedBox(height: 12), Align(alignment: Alignment.centerLeft, child: child)]))])));
}
