import logging
import os
import json
from datetime import datetime


class AILogger:
    def __init__(self, log_dir=None):
        # Usar diretório relativo dentro do projeto para evitar problemas de permissão
        if log_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(current_dir)
            log_dir = os.path.join(base_dir, "app_logs")

        try:
            # Criar diretório de logs se não existir
            os.makedirs(log_dir, exist_ok=True)

            # Configurar logger principal
            self.logger = logging.getLogger("ai_agents")
            self.logger.setLevel(logging.INFO)

            # Limpar handlers existentes para evitar duplicação
            self.logger.handlers.clear()

            # Configurar manipulador de arquivos
            log_file = os.path.join(
                log_dir, f"ai_agents_{datetime.now().strftime('%Y%m%d')}.log")
            try:
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.INFO)

                # Formato detalhado para arquivo
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                file_handler.setFormatter(file_formatter)

                self.logger.addHandler(file_handler)

                # Configurar console handler com formato mais amigável
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.INFO)

                # Formato especial para console - mais legível para chamadas de tools
                console_formatter = logging.Formatter(
                    '\n🔧 [TOOL CALL] %(message)s\n')
                console_handler.setFormatter(console_formatter)

                self.logger.addHandler(console_handler)

                self.log_dir = log_dir
                self.initialized = True
                print(
                    f"Logger inicializado com sucesso. Logs serão salvos em: {log_dir}")

            except PermissionError:
                print(
                    f"AVISO: Permissão negada para escrever logs em {log_file}. Usando apenas logs do console.")
                console_handler = logging.StreamHandler()
                console_formatter = logging.Formatter(
                    '\n🔧 [TOOL CALL] %(message)s\n')
                console_handler.setFormatter(console_formatter)
                self.logger.addHandler(console_handler)
                self.initialized = False
                self.log_dir = None

        except Exception as e:
            print(
                f"AVISO: Erro ao inicializar logger: {e}. Apenas logs do console serão usados.")
            self.logger = logging.getLogger("ai_agents")
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '\n🔧 [TOOL CALL] %(message)s\n')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
            self.initialized = False
            self.log_dir = None

    def log_agent_call(self, agent_name, method_name, input_data=None, output_data=None, error=None):
        """Registra uma chamada a um agente de IA"""
        # Formatar mensagem para console de forma mais legível
        console_message = f"Agent: {agent_name}\nMethod: {method_name}"
        if input_data:
            console_message += f"\nInput: {json.dumps(input_data, indent=2, ensure_ascii=False)}"
        if output_data:
            console_message += f"\nOutput: {json.dumps(output_data, indent=2, ensure_ascii=False)}"
        if error:
            console_message += f"\nError: {error}"

        # Log para console
        if error:
            self.logger.error(console_message)
        else:
            self.logger.info(console_message)

        # Log detalhado como JSON
        if self.initialized and self.log_dir:
            try:
                log_data = {
                    "timestamp": datetime.now().isoformat(),
                    "agent": agent_name,
                    "method": method_name,
                    "input": input_data,
                    "output": output_data,
                    "error": str(error) if error else None,
                    "success": error is None
                }

                detailed_log_file = os.path.join(
                    self.log_dir, "detailed_calls.json")
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

        # Log para console com emoji
        console_message = f"🎤 STT Event:\nUser: {user_id}\nWord: {word}\nSuccess: {success}"
        self.logger.info(console_message)

        # Log detalhado como JSON
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
    print(
        f"AVISO: Erro ao criar instância do logger: {e}. Usando um logger alternativo básico.")
    ai_logger = logging.getLogger("fallback_logger")
    handler = logging.StreamHandler()
    formatter = logging.Formatter('\n🔧 [TOOL CALL] %(message)s\n')
    handler.setFormatter(formatter)
    ai_logger.addHandler(handler)

    def simple_log_agent_call(agent_name, method_name, **kwargs):
        print(f"\n🔧 [TOOL CALL] {agent_name}.{method_name}\n")

    def simple_log_stt_event(user_id, exercise_id, word, transcript, success):
        print(f"\n🎤 [STT] User {user_id}, Word: {word}, Success: {success}\n")

    ai_logger.log_agent_call = simple_log_agent_call
    ai_logger.log_stt_event = simple_log_stt_event
