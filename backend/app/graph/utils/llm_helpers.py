"""
LLM 호출 관련 헬퍼 함수들
"""
import json
import logging
import requests
from typing import List, Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


def extract_json_from_response(content: str) -> str:
    """LLM 응답에서 JSON 추출"""
    if "```json" in content:
        return content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        return content.split("```")[1].split("```")[0].strip()
    return content.strip()


class OpenAIClient:
    """OpenAI API 클라이언트 클래스"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
    
    def call(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        use_responses_api: bool = False
    ) -> str:
        """
        OpenAI API 호출
        
        Args:
            messages: 메시지 리스트
            model: 모델명
            temperature: temperature 파라미터
            use_responses_api: /v1/responses API 사용 여부 (베타)
        
        Returns:
            API 응답 내용
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        if use_responses_api:
            # /v1/responses API 사용 (베타)
            url = "https://api.openai.com/v1/responses"
            # TODO: /v1/responses API 형식에 맞게 수정 필요
            # 현재는 형식 불명확하므로 일단 주석 처리
            payload = {
                "model": model,
                "input": messages[-1]["content"] if messages else "",
            }
            logger.warning("/v1/responses API는 아직 구현되지 않았습니다. /v1/chat/completions를 사용합니다.")
            use_responses_api = False
        
        if not use_responses_api:
            # /v1/chat/completions API 사용 (헤더 최소화로 헤더 불일치 문제 해결)
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            if use_responses_api:
                # /v1/responses 응답 형식 처리 (TODO)
                return result.get("output", "")
            else:
                # /v1/chat/completions 응답 형식 처리
                return result["choices"][0]["message"]["content"].strip()
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API 호출 오류: {e}")
            raise


def call_openai_api(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    use_responses_api: bool = False
) -> str:
    """
    OpenAI API 호출 헬퍼 함수 (하위 호환성을 위한 함수)
    use_responses_api=True일 때 /v1/responses 사용 (베타)
    use_responses_api=False일 때 /v1/chat/completions 사용 (헤더 최소화)
    """
    client = OpenAIClient()
    return client.call(messages, model, temperature, use_responses_api)

