# backend/pedidos/middleware.py
from django.utils.deprecation import MiddlewareMixin

class FeedbackMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if hasattr(request, "_feedback"):
            response.data = response.data or {}
            response.data["feedback"] = request._feedback
        return response
