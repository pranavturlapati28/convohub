import os
from typing import List, Dict, Any, Optional
from app.core.settings import settings

# Try to import OpenAI, fallback to echo if not available
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

def assistant_reply(history: list[dict]) -> str:
    """Generate assistant reply using OpenAI or fallback to echo."""
    if not OPENAI_AVAILABLE:
        # Fallback to echo if OpenAI not available
        last_user = next((m["content"] for m in reversed(history) if m.get("role")=="user"), "")
        return f"(echo) You said: {str(last_user)[:200]}"
    
    try:
        # Use OpenAI API
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Convert history to OpenAI format
        messages = []
        for msg in history:
            if isinstance(msg.get("content"), dict):
                content = msg["content"].get("text", "")
            else:
                content = str(msg.get("content", ""))
            
            messages.append({
                "role": msg.get("role", "user"),
                "content": content
            })
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        # Fallback to echo if API call fails
        print(f"OpenAI API error: {e}")
        last_user = next((m["content"] for m in reversed(history) if m.get("role")=="user"), "")
        return f"(echo) You said: {str(last_user)[:200]}"


def estimate_tokens(text: str | dict | None) -> int:
    """Very rough token estimator to help trim context.

    Assumes ~4 characters per token. If a dict is passed, will try to use
    the 'text' field.
    """
    if text is None:
        return 0
    if isinstance(text, dict):
        text = text.get("text", "")
    s = str(text)
    if not s:
        return 0
    # 1 token ~= 4 characters heuristic
    return max(1, len(s) // 4)
