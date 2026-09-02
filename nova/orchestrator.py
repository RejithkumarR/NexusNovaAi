from .models import NovaModel, NovaResponse
from .router import CapabilityRouter, RequestContext


class NovaOrchestrator:
    def __init__(self, model: NovaModel, router: CapabilityRouter | None = None):
        self.model = model
        self.router = router or CapabilityRouter()

    def run(self, request: RequestContext) -> NovaResponse:
        capability = self.router.route(request)
        if capability == "chat":
            return self.model.generate(request.text)

        return NovaResponse(
            text=f"Capability '{capability}' is routed but its provider is not configured yet.",
            capability=capability,
            model=self.model.name,
            metadata={"status": "provider_required"},
        )
