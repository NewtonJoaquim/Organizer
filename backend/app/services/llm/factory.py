from app.core.config import settings
from app.services.llm.base import BaseLLMProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.mock_provider import MockLLMProvider
from app.services.llm.openai_provider import OpenAIProvider


def get_llm_provider() -> BaseLLMProvider:
    """
    Retorna a instância do provedor LLM configurado.
    Se uma chave OpenAI estiver presente e o provedor não for forçado para 'mock',
    ativa automaticamente o OpenAIProvider com chamadas reais ao GPT-4o-mini.
    """
    provider_name = settings.LLM_PROVIDER.lower()

    if provider_name == "mock":
        return MockLLMProvider()

    # Prioriza OpenAI se chave estiver configurada
    if settings.OPENAI_API_KEY and (provider_name in ["openai", "auto", "default"] or provider_name == "mock" and settings.OPENAI_API_KEY):
        return OpenAIProvider()

    # Suporte a Gemini
    if settings.GEMINI_API_KEY and provider_name == "gemini":
        return GeminiProvider()

    if settings.OPENAI_API_KEY:
        return OpenAIProvider()

    # Fallback seguro para desenvolvimento local sem custos
    return MockLLMProvider()
