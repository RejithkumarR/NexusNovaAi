import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

const apiBaseUrl = String.fromEnvironment('NOVA_API_URL', defaultValue: 'http://10.0.2.2:8000');

void main() => runApp(const NovaApp());

class NovaApp extends StatelessWidget {
  const NovaApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'NOVA AI',
        theme: ThemeData(useMaterial3: true, colorSchemeSeed: Colors.deepPurple),
        home: const NovaHomePage(),
      );
}

class NovaHomePage extends StatefulWidget {
  const NovaHomePage({super.key});
  @override
  State<NovaHomePage> createState() => _NovaHomePageState();
}

class _NovaHomePageState extends State<NovaHomePage> with SingleTickerProviderStateMixin {
  final controller = TextEditingController();
  final messages = <Map<String, String>>[];
  late final TabController tabs = TabController(length: 2, vsync: this);
  bool busy = false;
  String status = 'Ready';

  Future<void> sendMessage() async {
    final text = controller.text.trim();
    if (text.isEmpty || busy) return;
    setState(() { busy = true; messages.add({'role': 'user', 'text': text}); controller.clear(); });
    try {
      final response = await http.post(
        Uri.parse('$apiBaseUrl/v1/chat'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'message': text}),
      );
      if (response.statusCode >= 300) throw Exception(response.body);
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      setState(() => messages.add({'role': 'assistant', 'text': '${data['text']}'}));
    } catch (e) {
      setState(() => messages.add({'role': 'assistant', 'text': 'Connection error: $e'}));
    } finally { setState(() => busy = false); }
  }

  Future<void> uploadTrainingData() async {
    final result = await FilePicker.platform.pickFiles(withData: true, type: FileType.custom, allowedExtensions: ['csv', 'xlsx', 'md']);
    if (result == null) return;
    final file = result.files.single;
    if (file.bytes == null) { setState(() => status = 'Could not read the selected file'); return; }
    setState(() => status = 'Uploading ${file.name}...');
    try {
      final request = http.MultipartRequest('POST', Uri.parse('$apiBaseUrl/v1/datasets/upload'));
      request.files.add(http.MultipartFile.fromBytes('file', file.bytes!, filename: file.name));
      final response = await request.send();
      final body = await response.stream.bytesToString();
      if (response.statusCode >= 300) throw Exception(body);
      setState(() => status = 'Uploaded: ${file.name}. Dataset is ready for preparation/training.');
    } catch (e) { setState(() => status = 'Upload failed: $e'); }
  }

  Future<void> prepare() async {
    setState(() => status = 'Preparing datasets...');
    try {
      final response = await http.post(Uri.parse('$apiBaseUrl/v1/datasets/prepare'));
      if (response.statusCode >= 300) throw Exception(response.body);
      final data = jsonDecode(response.body);
      setState(() => status = 'Prepared ${data['records']} training records.');
    } catch (e) { setState(() => status = 'Prepare failed: $e'); }
  }

  Future<void> train() async {
    setState(() => status = 'Starting training job...');
    try {
      final response = await http.post(Uri.parse('$apiBaseUrl/v1/train'), headers: {'Content-Type': 'application/json'}, body: jsonEncode({}));
      if (response.statusCode >= 300) throw Exception(response.body);
      final data = jsonDecode(response.body);
      setState(() => status = 'Training started (PID ${data['pid'] ?? 'server job'}).');
    } catch (e) { setState(() => status = 'Training failed to start: $e'); }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('NOVA AI'), bottom: TabBar(controller: tabs, tabs: const [Tab(text: 'Chat'), Tab(text: 'Train')])),
        body: TabBarView(controller: tabs, children: [
          Column(children: [
            Expanded(child: ListView.builder(padding: const EdgeInsets.all(12), itemCount: messages.length, itemBuilder: (_, i) {
              final item = messages[i];
              return Align(alignment: item['role'] == 'user' ? Alignment.centerRight : Alignment.centerLeft, child: Card(child: Padding(padding: const EdgeInsets.all(12), child: Text(item['text']!))));
            })),
            SafeArea(child: Row(children: [Expanded(child: TextField(controller: controller, onSubmitted: (_) => sendMessage(), decoration: const InputDecoration(hintText: 'Ask NOVA...', border: OutlineInputBorder()))), const SizedBox(width: 8), IconButton(onPressed: busy ? null : sendMessage, icon: const Icon(Icons.send))]))
          ]),
          Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            const Text('Training data', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            const Text('Upload CSV, Excel (.xlsx), or Markdown (.md). The server publishes the original file to the NOVA GitHub dataset folder when GitHub credentials are configured.'),
            const SizedBox(height: 20),
            FilledButton.icon(onPressed: uploadTrainingData, icon: const Icon(Icons.upload_file), label: const Text('Upload training data')),
            OutlinedButton.icon(onPressed: prepare, icon: const Icon(Icons.dataset), label: const Text('Prepare JSONL')),
            FilledButton.icon(onPressed: train, icon: const Icon(Icons.model_training), label: const Text('Start LoRA training')),
            const SizedBox(height: 20),
            Text(status),
          ]))
        ]),
      );
}
