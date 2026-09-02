from typing import Any

from .config import get_settings
from .models import NovaModel, NovaResponse


class LocalTransformerModel(NovaModel):
    """Self-hosted causal language model loaded from a local NOVA checkpoint.

    No hosted inference API is used. Model weights must already exist on the
    machine and are referenced through NOVA_MODEL_PATH.
    """

    name = "nova-local"

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or get_settings().model_path
        self._tokenizer: Any = None
        self._model: Any = None

    def _load(self) -> None:
        if self._model is not None:
            return
        if not self.model_path:
            raise RuntimeError(
                "NOVA_MODEL_PATH is not configured. Point it to the local NOVA model checkpoint."
            )

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "Local model support requires the ML dependencies. Install: pip install -e '.[ml]'"
            ) from exc

        tokenizer = AutoTokenizer.from_pretrained(self.model_path, local_files_only=True)
        load_kwargs: dict[str, Any] = {"local_files_only": True}
        settings = get_settings()
        if settings.device == "auto":
            load_kwargs["device_map"] = "auto"
        else:
            load_kwargs["device_map"] = settings.device
        load_kwargs["torch_dtype"] = "auto"

        model = AutoModelForCausalLM.from_pretrained(self.model_path, **load_kwargs)
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token

        self._tokenizer = tokenizer
        self._model = model

    def generate(self, prompt: str, **kwargs: Any) -> NovaResponse:
        self._load()
        settings = get_settings()

        messages = [{"role": "user", "content": prompt}]
        tokenizer = self._tokenizer
        model = self._model

        if getattr(tokenizer, "chat_template", None):
            inputs = tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                return_tensors="pt",
            )
            if hasattr(inputs, "to"):
                inputs = inputs.to(model.device)
        else:
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        max_new_tokens = int(kwargs.get("max_new_tokens", settings.max_new_tokens))
        temperature = float(kwargs.get("temperature", settings.temperature))
        do_sample = temperature > 0

        generation_kwargs: dict[str, Any] = {
            "max_new_tokens": max_new_tokens,
            "do_sample": do_sample,
            "pad_token_id": tokenizer.pad_token_id,
        }
        if do_sample:
            generation_kwargs["temperature"] = temperature

        with __import__("torch").inference_mode():
            output = model.generate(**inputs, **generation_kwargs)

        input_length = inputs["input_ids"].shape[-1] if isinstance(inputs, dict) else inputs.shape[-1]
        generated = output[0][input_length:]
        text = tokenizer.decode(generated, skip_special_tokens=True).strip()

        return NovaResponse(
            text=text,
            capability="chat",
            model=self.name,
            metadata={"provider": "self_hosted", "model_path": self.model_path},
        )
