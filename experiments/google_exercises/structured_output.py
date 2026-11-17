"""PROCEDURAL: reproducible Gemini structured-output exercise over local HTTP."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from threading import Thread

from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError


class ArrivalUpdate(BaseModel):
    flight: str
    status: str
    release_confirmed: bool


fixture = {"flight": "EXAMPLE01", "status": "inspection pending", "release_confirmed": False}


class FixtureServer(BaseHTTPRequestHandler):
    request_contract = None

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        contract = body["generationConfig"]
        self.__class__.request_contract = {
            "jsonMode": contract["responseMimeType"] == "application/json",
            "requestedFields": sorted(contract["responseJsonSchema"]["properties"]),
        }
        output = json.dumps({"candidates": [{
            "content": {"role": "model", "parts": [{"text": json.dumps(fixture)}]},
            "finishReason": "STOP",
        }]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(output)))
        self.end_headers()
        self.wfile.write(output)

    def log_message(self, *_):
        pass


def main():
    with HTTPServer(("127.0.0.1", 0), FixtureServer) as server:
        thread = Thread(target=server.serve_forever)
        thread.start()
        try:
            with genai.Client(api_key="local-fixture", http_options=types.HttpOptions(
                base_url=f"http://127.0.0.1:{server.server_port}", api_version="v1beta",
            )) as client:
                response = client.models.generate_content(
                    model="local-fixture-model",
                    contents="EXAMPLE01 is waiting for inspection. Release remains unconfirmed.",
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_json_schema=ArrivalUpdate.model_json_schema(),
                    ),
                )
            result = ArrivalUpdate.model_validate_json(response.text)
            try:
                ArrivalUpdate.model_validate({"flight": fixture["flight"], "status": fixture["status"]})
            except ValidationError:
                missing_field_rejected = True
            else:
                raise AssertionError("Response without release confirmation field was accepted")
            if not FixtureServer.request_contract["jsonMode"] or result.model_dump() != fixture:
                raise AssertionError("Structured-output exercise failed")
            print(json.dumps({
                "transport": "Google Gen AI SDK with local fixture",
                "request": FixtureServer.request_contract,
                "parsed": result.model_dump(),
                "missingFieldRejected": missing_field_rejected,
            }, indent=2))
        finally:
            server.shutdown()
            thread.join()


if __name__ == "__main__":
    main()
