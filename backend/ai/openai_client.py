from openai import OpenAI  # Importe a classe OpenAI
import os
import logging

logger = logging.getLogger(__name__)

def create_openai_client(api_key=None):
    """
    Cria e retorna uma instância do cliente OpenAI.
    
    Args:
        api_key (str, optional): Chave de API da OpenAI.
        
    Returns:
        OpenAI: Uma instância do cliente OpenAI.
    """
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY não encontrada")
            print("Aviso: OPENAI_API_KEY não encontrada. Funcionamento offline.")
            return None
    
    try:
        print("Inicializando cliente OpenAI...")
        print(f"API Key: {api_key[:5]}...")
        
        # Criar e retornar o cliente
        client = OpenAI(api_key=api_key)
        logger.info("Cliente OpenAI inicializado com sucesso")
        print("Cliente OpenAI inicializado com sucesso")
        return client
    except Exception as e:
        logger.error(f"Erro ao inicializar cliente OpenAI: {str(e)}")
        print(f"Aviso: Cliente OpenAI não disponível. Modo offline ativado.")
        return None