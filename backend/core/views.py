# pyrefly: ignore [missing-import]
from rest_framework.decorators import api_view
# pyrefly: ignore [missing-import]
from rest_framework.response import Response


@api_view(["GET"])
def health_check(request):
    """Simple health check endpoint."""
    return Response({"status": "ok"})
