from __future__ import annotations

import json

from app.config import Settings


def enhance_fields(settings: Settings, document_type: str, text: str, rule_fields: dict) -> tuple[dict, str]:
    """Optionally fill missing fields with Azure OpenAI; rules remain the baseline."""
    if not settings.azure_openai_enabled:
        return rule_fields, "rules"
    required = (settings.azure_openai_endpoint, settings.azure_openai_api_key, settings.azure_openai_deployment)
    if not all(required):
        raise RuntimeError("Azure OpenAI is enabled but endpoint, key, or deployment is missing")

    from openai import AzureOpenAI

    client = AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )
    response = client.chat.completions.create(
        model=settings.azure_openai_deployment,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract document fields into one flat JSON object. Return only facts present in the text. "
                    "Use ISO YYYY-MM-DD dates, numeric amounts, and null for unknown values."
                ),
            },
            {
                "role": "user",
                "content": f"Document type: {document_type}\nKnown rule fields: {json.dumps(rule_fields)}\n\n{text[:12000]}",
            },
        ],
    )
    parsed = json.loads(response.choices[0].message.content or "{}")
    merged = dict(rule_fields)
    for key, value in parsed.items():
        if value not in (None, "") and key not in merged:
            merged[key] = value
    return merged, "rules+azure_openai"

