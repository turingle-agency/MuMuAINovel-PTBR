import httpx
import pytest

from app.services.radar_collectors.youtube import YouTubeCommentsCollector
from tests.test_radar_firecrawl import CONTEXT, INPUT


@pytest.mark.asyncio
async def test_youtube_video_limits_and_disabled_comments():
    requests = []

    def handle(request):
        requests.append(request)
        assert request.headers["x-goog-api-key"] == "chave-fake"
        if request.url.path.endswith("/search"):
            return httpx.Response(200, json={"items": [
                {"id": {"videoId": f"v{i}"}, "snippet": {
                    "title": f"Vídeo {i}", "publishedAt": "2026-11-01T12:00:00Z",
                }}
                for i in range(6)
            ]})
        if request.url.params["videoId"] == "v1":
            return httpx.Response(403, json={"error": {"errors": [{"reason": "commentsDisabled"}]}})
        vid = request.url.params["videoId"]
        return httpx.Response(200, json={"items": [
            {"snippet": {"topLevelComment": {"id": f"{vid}-c{i}", "snippet": {
                "textDisplay": "Meu comentário", "authorDisplayName": "Não guardar",
                "publishedAt": "2026-11-12T12:00:00Z",
            }}}}
            for i in range(12)
        ]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await YouTubeCommentsCollector(client).collect(INPUT, CONTEXT)

    search, *comments = requests
    assert search.url.params["regionCode"] == "BR"
    assert search.url.params["relevanceLanguage"] == "pt"
    assert search.url.params["maxResults"] == "5"
    assert len(comments) == 5
    assert all(r.url.params["maxResults"] == "10" and r.url.params["textFormat"] == "plainText" for r in comments)
    assert result.status == "partial"
    assert "país dos autores" in " ".join(result.limits.notes)
    assert "desativados" in " ".join(result.limits.notes)
    assert len([item for item in result.items if item.data.excerpt]) == 40
    assert "Não guardar" not in result.model_dump_json()
    assert any(item.url.endswith("v=v4&lc=v4-c0") for item in result.items)


@pytest.mark.asyncio
@pytest.mark.parametrize(("response", "status", "note"), [
    (401, "error", "credencial"), (429, "error", "limite"), (None, "error", "tempo"),
    (200, "empty", None),
])
async def test_provider_errors_are_distinct_from_empty(response, status, note):
    def handle(request):
        if response is None:
            raise httpx.ReadTimeout("segredo", request=request)
        return httpx.Response(response, json={"items": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await YouTubeCommentsCollector(client).collect(INPUT, CONTEXT)
    assert result.status == status
    assert result.items == []
    if note:
        assert note in " ".join(result.limits.notes).lower()
    assert "segredo" not in result.model_dump_json()
