def websocket_bearer(subprotocols: list[str]) -> str | None:
    if len(subprotocols) >= 2 and subprotocols[0] == "apexgrid.jwt" and subprotocols[1]:
        return subprotocols[1]
    return None
