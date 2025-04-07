from openai import OpenAI
import os
import logging

logger = logging.getLogger(__name__)

def create_openai_client(api_key=None):
    """
    Cria uma instância do cliente OpenAI de forma segura, lidando com diferentes versões e configurações.
    
    Args:
        api_key (str, optional): Chave de API da OpenAI. Se não fornecida, será buscada nas variáveis de ambiente.
        
    Returns:
        OpenAI: Uma instância inicializada do cliente OpenAI.
    """
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY não encontrada nas variáveis de ambiente")
            raise ValueError("OPENAI_API_KEY não fornecida e não encontrada nas variáveis de ambiente")
    
    try:
        # Versão moderna do cliente OpenAI (1.0.0+)
        client = OpenAI(api_key=api_key)
        logger.info("Cliente OpenAI inicializado com sucesso (versão moderna)")
        return client
    except Exception as e:
        logger.error(f"Erro ao inicializar cliente OpenAI: {str(e)}")
        raise