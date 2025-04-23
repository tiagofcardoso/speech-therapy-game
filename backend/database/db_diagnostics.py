"""
Ferramentas de diagnóstico para o conector de banco de dados.
Este módulo ajuda a identificar e resolver problemas com o acesso ao banco de dados.
"""

import traceback
import json
from bson import ObjectId, json_util


class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def diagnose_db_connector(db_connector):
    """
    Diagnóstico do conector de banco de dados, verificando seu estado
    e conexões às coleções.
    """
    results = {
        "status": "unknown",
        "collections": {},
        "methods": {},
        "error": None
    }

    try:
        # Verificar se o conector existe e tem as coleções esperadas
        if not db_connector:
            results["status"] = "failed"
            results["error"] = "DB connector is None"
            return results

        # Verificar as coleções
        collections = [
            "users_collection",
            "games_collection",
            "sessions_collection"
        ]

        for collection_name in collections:
            if hasattr(db_connector, collection_name):
                collection = getattr(db_connector, collection_name)
                if collection:
                    # Tentar contar documentos para verificar conexão
                    try:
                        count = collection.count_documents({})
                        results["collections"][collection_name] = {
                            "status": "ok",
                            "count": count
                        }
                    except Exception as e:
                        results["collections"][collection_name] = {
                            "status": "error",
                            "error": str(e)
                        }
                else:
                    results["collections"][collection_name] = {
                        "status": "missing",
                        "error": f"Collection {collection_name} is None"
                    }
            else:
                results["collections"][collection_name] = {
                    "status": "not_found",
                    "error": f"Collection {collection_name} not found in connector"
                }

        # Verificar métodos essenciais
        methods = [
            "get_game",
            "get_user_by_id",
            "get_session",
            "store_game"
        ]

        for method_name in methods:
            if hasattr(db_connector, method_name):
                method = getattr(db_connector, method_name)
                if callable(method):
                    results["methods"][method_name] = {
                        "status": "ok"
                    }
                else:
                    results["methods"][method_name] = {
                        "status": "not_callable",
                        "error": f"Method {method_name} exists but is not callable"
                    }
            else:
                results["methods"][method_name] = {
                    "status": "not_found",
                    "error": f"Method {method_name} not found in connector"
                }

        # Status geral
        if all(c["status"] == "ok" for c in results["collections"].values()) and \
           all(m["status"] == "ok" for m in results["methods"].values()):
            results["status"] = "ok"
        else:
            results["status"] = "issues_found"

    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        results["traceback"] = traceback.format_exc()

    return results


def test_get_game(db_connector, game_id):
    """
    Testa a função get_game com um ID de jogo específico e retorna detalhes do resultado.
    """
    results = {
        "status": "unknown",
        "error": None,
        "game": None,
        "game_id": game_id,
        "details": {}
    }

    try:
        # Verificar o formato do ID
        results["details"]["id_format"] = {}
        try:
            if ObjectId.is_valid(game_id):
                results["details"]["id_format"]["valid_objectid"] = True
                object_id = ObjectId(game_id)
                results["details"]["id_format"]["object_id"] = str(object_id)
            else:
                results["details"]["id_format"]["valid_objectid"] = False
                results["details"]["id_format"]["error"] = "Not a valid ObjectId"
        except Exception as id_error:
            results["details"]["id_format"]["valid_objectid"] = False
            results["details"]["id_format"]["error"] = str(id_error)

        # Tentar buscar o jogo usando o método do conector
        if hasattr(db_connector, 'get_game') and callable(db_connector.get_game):
            try:
                game = db_connector.get_game(game_id)
                results["details"]["get_game"] = {
                    "status": "called",
                    "returned": game is not None
                }

                if game:
                    # Converter ObjectId para string no resultado
                    game_dict = {k: str(v) if isinstance(
                        v, ObjectId) else v for k, v in game.items()}
                    results["game"] = game_dict
                    results["status"] = "found"
                else:
                    results["status"] = "not_found"

            except Exception as get_error:
                results["details"]["get_game"] = {
                    "status": "error",
                    "error": str(get_error),
                    "traceback": traceback.format_exc()
                }
                results["status"] = "error"
                results["error"] = f"Error in get_game: {str(get_error)}"
        else:
            results["details"]["get_game"] = {
                "status": "not_available",
                "error": "Method get_game not found or not callable"
            }
            results["status"] = "missing_method"
            results["error"] = "Method get_game not available in DB connector"

        # Tentar buscar diretamente da coleção
        if hasattr(db_connector, 'games_collection'):
            collection = db_connector.games_collection
            if collection:
                try:
                    # Buscar por _id se for um ObjectId válido
                    query_results = []
                    if ObjectId.is_valid(game_id):
                        game_obj = collection.find_one(
                            {"_id": ObjectId(game_id)})
                        if game_obj:
                            query_results.append(("_id", game_obj))

                    # Buscar também por _id como string
                    game_obj = collection.find_one({"_id": game_id})
                    if game_obj:
                        query_results.append(("_id_string", game_obj))

                    # Buscar por game_id como campo
                    game_obj = collection.find_one({"game_id": game_id})
                    if game_obj:
                        query_results.append(("game_id", game_obj))

                    results["details"]["direct_query"] = {
                        "status": "executed",
                        "results": [
                            {
                                "query_type": qtype,
                                "found": True,
                                "id": str(obj.get("_id", "unknown"))
                            }
                            for qtype, obj in query_results
                        ]
                    }

                    # Se não encontramos via get_game mas encontramos diretamente, atualizar status
                    if results["status"] == "not_found" and query_results:
                        results["status"] = "found_direct"
                        # Usar o primeiro resultado encontrado
                        if not results["game"]:
                            game_dict = {k: str(v) if isinstance(v, ObjectId) else v
                                         for k, v in query_results[0][1].items()}
                            results["game"] = game_dict
                            results["details"]["recovery_method"] = query_results[0][0]

                except Exception as query_error:
                    results["details"]["direct_query"] = {
                        "status": "error",
                        "error": str(query_error),
                        "traceback": traceback.format_exc()
                    }
            else:
                results["details"]["direct_query"] = {
                    "status": "not_available",
                    "error": "Collection is None"
                }
        else:
            results["details"]["direct_query"] = {
                "status": "not_available",
                "error": "games_collection not found in DB connector"
            }

    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        results["traceback"] = traceback.format_exc()

    return results


def test_tts_service(db_connector, text="Teste de áudio"):
    """
    Testa o serviço de síntese de voz e retorna detalhes do resultado.
    """
    results = {
        "status": "unknown",
        "error": None,
        "audio_generated": False,
        "audio_size": 0,
        "test_text": text,
        "details": {}
    }

    try:
        # Importar o serviço de TTS se disponível
        try:
            from ..services.tts_service import generate_speech
            results["details"]["import"] = {
                "status": "success"
            }
        except ImportError as e:
            results["details"]["import"] = {
                "status": "failed",
                "error": str(e)
            }
            results["status"] = "error"
            results["error"] = f"Failed to import TTS service: {str(e)}"
            return results

        # Tentar gerar áudio
        try:
            audio_data = generate_speech(text)
            if audio_data:
                results["audio_generated"] = True
                results["audio_size"] = len(audio_data)
                results["details"]["generation"] = {
                    "status": "success",
                    "length": len(audio_data)
                }

                # Verificar a codificação do áudio e adicionar base64 para testes
                import base64
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                results["details"]["audio_playable"] = {
                    "format": "base64",
                    "prefix": "data:audio/mp3;base64,",
                    "sample": audio_b64[:100] + "..." if len(audio_b64) > 100 else audio_b64
                }

                # Adicionar um HTML de teste para reproduzir o áudio
                audio_html = f'<audio controls src="data:audio/mp3;base64,{audio_b64}"></audio>'
                results["details"]["test_player"] = audio_html

                # Incluir uma amostra do início do áudio para debug
                results["details"]["audio_sample"] = str(
                    audio_data[:100]) + "..."
                results["status"] = "ok"
            else:
                results["details"]["generation"] = {
                    "status": "empty",
                    "error": "Audio data is empty or None"
                }
                results["status"] = "failed"
        except Exception as gen_error:
            results["details"]["generation"] = {
                "status": "error",
                "error": str(gen_error),
                "traceback": traceback.format_exc()
            }
            results["status"] = "error"
            results["error"] = f"Error generating speech: {str(gen_error)}"

    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        results["traceback"] = traceback.format_exc()

    return results


def check_api_endpoints(app):
    """
    Verifica a configuração dos endpoints da API e retorna informações sobre suas rotas e métodos.
    """
    results = {
        "status": "unknown",
        "endpoints": {},
        "error": None,
        "fix_suggestions": []
    }

    try:
        if not app or not hasattr(app, 'url_map'):
            results["status"] = "error"
            results["error"] = "App object is invalid or does not have url_map"
            return results

        # Examine all routes in the Flask app
        found_game_finish = False
        for rule in app.url_map.iter_rules():
            endpoint = str(rule)
            methods = sorted(list(rule.methods))
            endpoint_info = {
                "endpoint": endpoint,
                "methods": methods,
                "handler": rule.endpoint,
                "path": str(rule)
            }

            # Adicionar informações adicionais para endpoints específicos
            if 'game/finish' in endpoint:
                found_game_finish = True
                endpoint_info["critical"] = True
                if 'POST' not in methods:
                    endpoint_info["issue"] = "POST method not allowed for game/finish endpoint"
                    results["fix_suggestions"].append({
                        "endpoint": endpoint,
                        "issue": "Missing POST method",
                        "suggestion": "Add @app.route('/api/game/finish', methods=['POST']) to your route declaration"
                    })

            results["endpoints"][endpoint] = endpoint_info

        # Verificar se o endpoint game/finish existe
        if not found_game_finish:
            results["fix_suggestions"].append({
                "issue": "Missing game/finish endpoint",
                "suggestion": "Create a route for /api/game/finish with POST method"
            })

        # Set overall status
        issues = [ep for ep in results["endpoints"].values()
                  if ep.get("issue")]
        if issues:
            results["status"] = "issues_found"
            results["issues_count"] = len(issues)
        else:
            results["status"] = "ok"

        # Adicionar código de exemplo para fix
        results["example_code"] = """
# Exemplo de implementação correta do endpoint de finalização de jogo
@app.route('/api/game/finish', methods=['POST'])
def finish_game():
    data = request.json
    # Processar a finalização do jogo
    # ...
    return jsonify({"success": True})
"""

    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        results["traceback"] = traceback.format_exc()

    return results


def initialize_debug_endpoints(app, db_connector):
    """
    Adiciona endpoints de debug à aplicação Flask para diagnosticar problemas de banco de dados.
    Apenas para uso em ambiente de desenvolvimento!
    """
    from flask import jsonify, request, Response

    @app.route('/api/debug/db-status', methods=['GET'])
    def debug_db_status():
        """Endpoint para verificar o status do banco de dados"""
        if app.config.get('ENV') != 'development':
            return jsonify({"error": "Debug endpoints only available in development"}), 403

        results = diagnose_db_connector(db_connector)
        return jsonify(results)

    @app.route('/api/debug/db-game/<game_id>', methods=['GET'])
    def debug_db_game(game_id):
        """Endpoint para testar a busca de um jogo específico"""
        if app.config.get('ENV') != 'development':
            return jsonify({"error": "Debug endpoints only available in development"}), 403

        results = test_get_game(db_connector, game_id)
        return jsonify(results)

    @app.route('/api/debug/tts-test', methods=['GET', 'POST'])
    def debug_tts():
        """Endpoint para testar a síntese de voz"""
        if app.config.get('ENV') != 'development':
            return jsonify({"error": "Debug endpoints only available in development"}), 403

        text = request.args.get('text', 'Teste de áudio do sistema')
        if request.method == 'POST' and request.json:
            text = request.json.get('text', text)

        results = test_tts_service(db_connector, text)
        return jsonify(results)

    @app.route('/api/debug/audio-player', methods=['GET'])
    def debug_audio_player():
        """Endpoint para testar a reprodução de áudio diretamente"""
        if app.config.get('ENV') != 'development':
            return jsonify({"error": "Debug endpoints only available in development"}), 403

        try:
            from ..services.tts_service import generate_speech
            import base64

            text = request.args.get('text', 'Teste de reprodução de áudio')
            audio_data = generate_speech(text)

            if audio_data:
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Teste de Reprodução de Áudio</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                        button {{ padding: 10px; margin: 10px 0; cursor: pointer; }}
                        pre {{ background: #f4f4f4; padding: 10px; overflow: auto; }}
                        .success {{ color: green; }}
                        .error {{ color: red; }}
                    </style>
                </head>
                <body>
                    <h1>Diagnóstico de Reprodução de Áudio</h1>
                    
                    <h2>1. Teste com elemento &lt;audio&gt;</h2>
                    <audio controls src="data:audio/mp3;base64,{audio_b64}"></audio>
                    
                    <h2>2. Teste com API JavaScript</h2>
                    <button id="playButton">Reproduzir com JavaScript</button>
                    <div id="status"></div>
                    
                    <h2>3. Código para o Frontend</h2>
                    <pre>
// Copie esta função para seu código
function playAudio(audioBase64) {{
  const audio = new Audio(`data:audio/mp3;base64,${{audioBase64}}`);
  
  audio.addEventListener('error', (e) => {{
    console.error('Erro ao reproduzir áudio:', e);
  }});
  
  audio.addEventListener('play', () => {{
    console.log('Áudio iniciou a reprodução');
  }});
  
  audio.play().catch(err => {{
    console.error('Erro na API de reprodução:', err);
  }});
}}
                    </pre>
                    
                    <h2>4. Dados do Áudio</h2>
                    <p>Tamanho: {len(audio_data)} bytes</p>
                    <p>Texto sintetizado: "{text}"</p>
                    
                    <script>
                        document.getElementById('playButton').addEventListener('click', function() {{
                            const statusElement = document.getElementById('status');
                            statusElement.innerHTML = '<p>Tentando reproduzir...</p>';
                            statusElement.className = '';
                            
                            try {{
                                const audio = new Audio('data:audio/mp3;base64,{audio_b64}');
                                
                                audio.addEventListener('error', (e) => {{
                                    console.error('Erro ao reproduzir áudio:', e);
                                    statusElement.innerHTML = '<p>Erro ao reproduzir áudio. Verifique o console.</p>';
                                    statusElement.className = 'error';
                                }});
                                
                                audio.addEventListener('play', () => {{
                                    statusElement.innerHTML = '<p>Áudio iniciou a reprodução!</p>';
                                    statusElement.className = 'success';
                                }});
                                
                                audio.play().catch(err => {{
                                    console.error('Erro na API de reprodução:', err);
                                    statusElement.innerHTML = '<p>Erro na API de reprodução: ' + err.message + '</p>';
                                    statusElement.className = 'error';
                                }});
                            }} catch (e) {{
                                statusElement.innerHTML = '<p>Exceção: ' + e.message + '</p>';
                                statusElement.className = 'error';
                                console.error(e);
                            }}
                        }});
                    </script>
                </body>
                </html>
                """
                return Response(html, mimetype='text/html')
            else:
                return jsonify({"error": "Failed to generate audio data"}), 500
        except Exception as e:
            return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

    @app.route('/api/debug/endpoints', methods=['GET'])
    def debug_endpoints():
        """Endpoint para verificar a configuração dos endpoints da API"""
        if app.config.get('ENV') != 'development':
            return jsonify({"error": "Debug endpoints only available in development"}), 403

        results = check_api_endpoints(app)
        return jsonify(results)

    @app.route('/api/debug/audio-response', methods=['GET'])
    def debug_audio_response():
        """Endpoint para diagnosticar a resposta de áudio"""
        if app.config.get('ENV') != 'development':
            return jsonify({"error": "Debug endpoints only available in development"}), 403

        results = test_audio_response(app)
        return jsonify(results)

    # Para fins de diagnóstico, adicione uma rota mock para o game/finish se ela não existir
    if not any('game/finish' in str(rule) and 'POST' in rule.methods for rule in app.url_map.iter_rules()):
        @app.route('/api/debug/game/finish', methods=['POST'])
        def debug_finish_game():
            """Endpoint de diagnóstico para finalização de jogo"""
            if app.config.get('ENV') != 'development':
                return jsonify({"error": "Debug endpoints only available in development"}), 403

            data = request.json or {}
            return jsonify({
                "success": True,
                "debug": True,
                "message": "Esta é uma implementação de diagnóstico do endpoint game/finish",
                "received_data": data
            })
        print("🛠️ DEBUG: Criado endpoint temporário /api/debug/game/finish para testes")

    print("🔧 Debug endpoints initialized at /api/debug/*")
    print("  - /api/debug/db-status")
    print("  - /api/debug/db-game/<game_id>")
    print("  - /api/debug/tts-test")
    print("  - /api/debug/audio-player (interface HTML para testar reprodução)")
    print("  - /api/debug/endpoints")
    print("  - /api/debug/audio-response")
