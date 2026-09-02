from dataclasses import dataclass


@dataclass(frozen=True)
class RequestContext:
    text: str = ""
    has_image: bool = False
    has_audio: bool = False
    has_video: bool = False


class CapabilityRouter:
    """Routes requests to a capability without coupling the API to model vendors."""

    def route(self, request: RequestContext) -> str:
        if request.has_video:
            return "video"
        if request.has_audio:
            return "audio"
        if request.has_image:
            return "vision"

        text = request.text.lower()
        if any(x in text for x in ("generate image", "create image", "draw", "illustration")):
            return "image_generation"
        if any(x in text for x in ("write code", "debug", "program", "implement", "refactor")):
            return "code"
        return "chat"
