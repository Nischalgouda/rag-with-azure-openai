# FastAPI basics

FastAPI is a Python web framework for building REST APIs. It uses type hints and Pydantic models to validate request bodies automatically and to generate interactive OpenAPI documentation at the /docs path.

Endpoints are declared with decorators such as @app.get and @app.post. Handlers declared with async def run on the event loop, while plain def handlers run in a thread pool, so blocking calls like database queries should not be placed inside async handlers.

For authentication, FastAPI provides security utilities for OAuth2 bearer tokens and API keys. Dependencies injected with Depends are the standard way to share logic such as verifying a token on many routes.

# Testing and errors

Use TestClient from FastAPI to call endpoints in tests without starting a server. Raise HTTPException with a status code to return errors; use 502 when an upstream service such as an LLM endpoint fails.
