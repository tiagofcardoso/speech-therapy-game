import logging
import os
import json
from datetime import datetime

class AILogger:
    def __init__(self, log_dir=None):
        # Usar diretório relativo dentro do projeto para evitar problemas de permissão
        if log_dir is None:
            # Obter o diretório atual e criar o diretório de logs dentro dele
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(current_dir)  # Subir um nível para a raiz do backend
            log_dir = os.path.join(base_dir, "app_logs")  # Usar um nome diferente para evitar conflitos
        
        try:
            # Criar diretório de logs se não existir
            os.makedirs(log_dir, exist_ok=True)
            
            # Configurar logger principal
            self.logger = logging.getLogger("ai_agents")
            self.logger.setLevel(logging.INFO)
            
            # Verificar se o logger já tem handlers para evitar duplicação
            if not self.logger.handlers:
                # Configurar manipulador de arquivos
                log_file = os.path.join(log_dir, f"ai_agents_{datetime.now().strftime('%Y%m%d')}.log")
                try:
                    file_handler = logging.FileHandler(log_file)
                    file_handler.setLevel(logging.INFO)
                    
                    # Configurar formato
                    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                    file_handler.setFormatter(formatter)
                    
                    # Adicionar manipulador ao logger
                    self.logger.addHandler(file_handler)
                    
                    # Também logar para o console
                    console_handler = logging.StreamHandler()
                    console_handler.setFormatter(formatter)
                    self.logger.addHandler(console_handler)
                    
                    self.log_dir = log_dir
                    self.initialized = True
                    print(f"Logger inicializado com sucesso. Logs serão salvos em: {log_dir}")
                except PermissionError:
                    print(f"AVISO: Permissão negada para escrever logs em {log_file}. Usando apenas logs do console.")
                    # Configurar apenas logging para console se o arquivo falhar
                    console_handler = logging.StreamHandler()
                    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                    console_handler.setFormatter(formatter)
                    self.logger.addHandler(console_handler)
                    self.initialized = False
                    self.log_dir = None
            else:
                self.initialized = True
                self.log_dir = log_dir
        except Exception as e:
            print(f"AVISO: Erro ao inicializar logger: {e}. Apenas logs do console serão usados.")
            self.logger = logging.getLogger("ai_agents")
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            self.initialized = False
            self.log_dir = None
    
    def log_agent_call(self, agent_name, method_name, input_data=None, output_data=None, error=None):
        """Registra uma chamada a um agente de IA"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "method": method_name,
            "input": input_data,
            "output": output_data,
            "error": str(error) if error else None,
            "success": error is None
        }
        
        # Log como texto para o arquivo de log
        if error:
            self.logger.error(f"Agent: {agent_name}, Method: {method_name}, Error: {error}")
        else:
            self.logger.info(f"Agent: {agent_name}, Method: {method_name}, Success: True")
        
        # Log detalhado como JSON somente se a inicialização completa funcionou
        if self.initialized and self.log_dir:
            try:
                detailed_log_file = os.path.join(self.log_dir, "detailed_calls.json")
                with open(detailed_log_file, "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception as e:
                self.logger.error(f"Failed to write detailed log: {e}")
    
    def log_stt_event(self, user_id, exercise_id, word, transcript, success):
        """Registra um evento de reconhecimento de fala"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "type": "stt",
            "user_id": user_id,
            "exercise_id": exercise_id,
            "target_word": word,
            "transcript": transcript,
            "success": success
        }
        
        self.logger.info(f"STT: User {user_id}, Exercise {exercise_id}, Word: {word}, Success: {success}")
        
        # Log detalhado como JSON somente se a inicialização completa funcionou
        if self.initialized and self.log_dir:
            try:
                stt_log_file = os.path.join(self.log_dir, "stt_events.json")
                with open(stt_log_file, "a") as f:
                    f.write(json.dumps(log_data) + "\n")
            except Exception as e:
                self.logger.error(f"Failed to write STT log: {e}")

# Instância global para uso em todo o aplicativo
try:
    ai_logger = AILogger()
except Exception as e:
    print(f"AVISO: Erro ao criar instância do logger: {e}. Usando um logger alternativo básico.")
    # Criar um logger simples que só imprime no console em caso de falha total
    ai_logger = logging.getLogger("fallback_logger")
    handler = logging.StreamHandler()
    ai_logger.addHandler(handler)
    
    # Substituir os métodos por versões simples que só imprimem no console
    def simple_log_agent_call(agent_name, method_name, **kwargs):
        print(f"[AGENT LOG] {agent_name}.{method_name}")
    
    def simple_log_stt_event(user_id, exercise_id, word, transcript, success):
        print(f"[STT LOG] User {user_id}, Word: {word}, Success: {success}")
    
    ai_logger.log_agent_call = simple_log_agent_call
    ai_logger.log_stt_event = simple_log_stt_event