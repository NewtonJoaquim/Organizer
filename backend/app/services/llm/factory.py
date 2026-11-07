from app.core.config import settings
from app.services.llm.base import BaseLLMProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.mock_provider import MockLLMProvider
from app.services.llm.openai_provider import OpenAIProvider


def get_llm_provider() -> BaseLLMProvider:
    """
    Retorna a instância do provedor LLM configurado.
    Prioriza OpenAI ou Gemini se as chaves estiverem presentes; caso contrário,
    utiliza o MockLLMProvider determinístico de alta fidelidade (zero custo e zero latência de rede).
    """
    provider_name = settings.LLM_PROVIDER.lower()

    if provider_name == "openai" and settings.OPENAI_API_KEY:
        return OpenAIProvider()
    elif provider_name == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider()

    # Padrão seguro para desenvolvimento, testes e CI
    return MockLLMProvider()
