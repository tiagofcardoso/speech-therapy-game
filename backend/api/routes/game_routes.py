@router.post("/games/create_session")
async def create_game_session(request: Request, user_id: str = Body(...)):
    mcp = get_mcp_system()  # Get MCP singleton
    db = get_db_connector()  # Get DB singleton

    # Get user profile from database
    user_profile = db.get_user(user_id)
    if not user_profile:
        raise HTTPException(status_code=404, detail="User not found")

    # Create game session using MCP
    session = await mcp.create_game_session(user_id, user_profile)

    return JSONResponse(content=session)


@router.post("/games/{session_id}/evaluate")
async def evaluate_pronunciation(
    request: Request,
    session_id: str,
    audio_file: UploadFile = File(...),
    expected_word: str = Form(...)
):
    mcp = get_mcp_system()
    db = get_db_connector()

    # Get session from database
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Evaluate pronunciation using MCP
    result = await mcp.evaluate_pronunciation(session["user_id"], audio_file, expected_word)

    return JSONResponse(content=result)


@router.post("/games/{session_id}/respond")
async def process_response(
    request: Request,
    session_id: str,
    response: str = Body(...),
    expected_text: str = Body(...)
):
    mcp = get_mcp_system()
    db = get_db_connector()

    # Get session from database
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Process response using MCP
    result = await mcp.process_user_response(
        user_id=session["user_id"],
        response=response,
        expected_text=expected_text,
        session_id=session_id
    )

    return JSONResponse(content=result)
