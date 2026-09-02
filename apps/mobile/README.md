# NOVA Mobile

Flutter client for NOVA chat and training-data management.

## Create the Flutter platform files

From `apps/mobile` run:

```bash
flutter create .
flutter pub get
flutter run --dart-define=NOVA_API_URL=http://10.0.2.2:8000
```

For a physical Android device, use the LAN address of the machine running the NOVA API instead of `10.0.2.2`.

The app provides:

- Chat with `POST /v1/chat`
- Upload `.csv`, `.xlsx`, and `.md` training files
- Normalize training data with `POST /v1/datasets/prepare`
- Start LoRA SFT training with `POST /v1/train`

Flutter's `http` package is used for network requests and multipart upload. Android builds need the INTERNET permission.
