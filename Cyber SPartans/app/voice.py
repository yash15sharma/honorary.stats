import os
import sys
import hashlib
import tempfile
import shutil
from pathlib import Path

from fastapi import APIRouter, Request, HTTPException, Response

# Add repository root to sys.path so root modules import cleanly
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    import voice_service
except ImportError:
    voice_service = None

router = APIRouter()

AUDIO_CACHE_DIR = REPO_ROOT / "audio_cache"
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/api/voice")
@router.post("/api/speak")
async def generate_voice(request: Request):
    """
    Synthesizes multilingual voice audio for informal workers using ElevenLabs.
    Strictly avoids gTTS and silent MP3 caching.
    
    Contract: { text: str, language: "en" | "hi" | "kn" }
    Returns: audio/mpeg (or HTTP 503 on missing key / generation failure)
    """
    # 1. Verify ElevenLabs API Key first
    api_key = (os.getenv("ELEVENLABS_API_KEY") or "").strip()
    if not api_key or api_key.startswith("your_") or len(api_key) < 5:
        raise HTTPException(
            status_code=503,
            detail="ElevenLabs API key is not configured. Set ELEVENLABS_API_KEY in .env."
        )

    if not voice_service:
        raise HTTPException(
            status_code=503,
            detail="Voice service module is unavailable."
        )

    try:
        body = await request.json()
    except Exception:
        body = {}

    text = str(body.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Missing required 'text' field.")

    language = str(body.get("language") or "en").strip().lower()
    if language not in ("en", "hi", "kn"):
        language = "en"

    # Voice ID from environment or default from voice_service
    voice_id = (os.getenv("ELEVENLABS_VOICE_ID") or getattr(voice_service, "DEFAULT_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")).strip()

    # Hash text + language + voice_id for disk caching
    cache_string = f"{text}:{language}:{voice_id}"
    cache_hash = hashlib.sha256(cache_string.encode("utf-8")).hexdigest()
    cached_file = AUDIO_CACHE_DIR / f"{cache_hash}_{language}.mp3"

    # 2. Return cached audio if previously generated and valid (> 1 KB)
    if cached_file.exists() and cached_file.stat().st_size > 1024:
        return Response(
            content=cached_file.read_bytes(),
            media_type="audio/mpeg",
            headers={
                "X-Audio-Cache": "HIT",
                "Content-Disposition": f'inline; filename="{cache_hash}_{language}.mp3"'
            }
        )

    # 3. Generate in a temporary directory to inspect status before caching
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = voice_service.generate_voice_output(
                text=text,
                card_id=cache_hash,
                language=language,
                output_dir=tmp_dir
            )

            # NEVER cache or serve fallback audio (which produces silent MP3s)
            if result.get("status") == "fallback":
                err_msg = result.get("error") or "ElevenLabs synthesis failed and produced fallback audio."
                raise HTTPException(status_code=503, detail=err_msg)

            audio_path = result.get("audio_path")
            if not audio_path or not os.path.exists(audio_path) or os.path.getsize(audio_path) <= 1024:
                raise HTTPException(
                    status_code=503,
                    detail="Audio generation failed or produced empty file."
                )

            # Save strictly valid MP3 to permanent cache
            shutil.copyfile(audio_path, cached_file)
            audio_bytes = cached_file.read_bytes()

            return Response(
                content=audio_bytes,
                media_type="audio/mpeg",
                headers={
                    "X-Audio-Cache": "MISS",
                    "Content-Disposition": f'inline; filename="{cache_hash}_{language}.mp3"'
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Voice synthesis error: {str(e)}"
        )
