from nova.models import EchoModel
from nova.orchestrator import NovaOrchestrator
from nova.router import CapabilityRouter, RequestContext


def test_chat_routes_to_chat():
    router = CapabilityRouter()
    assert router.route(RequestContext(text="hello")) == "chat"


def test_code_routes_to_code():
    router = CapabilityRouter()
    assert router.route(RequestContext(text="write code for an API")) == "code"


def test_image_routes_to_vision_when_image_is_attached():
    router = CapabilityRouter()
    assert router.route(RequestContext(has_image=True)) == "vision"


def test_echo_model_smoke():
    nova = NovaOrchestrator(EchoModel())
    result = nova.run(RequestContext(text="hello NOVA"))
    assert result.capability == "chat"
    assert "hello NOVA" in result.text
