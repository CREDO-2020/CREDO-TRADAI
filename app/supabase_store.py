import os
from typing import Any

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = Any

def get_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key or create_client is None:
        return None
    return create_client(url, key)

def enabled():
    return get_client() is not None

def get_user_from_access_token(access_token: str):
    client = get_client()
    if client is None or not access_token:
        return None
    try:
        result = client.auth.get_user(access_token)
        return result.user
    except Exception:
        return None

def get_demo_account(user_id: str):
    client = get_client()
    if client is None:
        return None
    result = client.table("demo_accounts").select("*").eq("user_id", user_id).limit(1).execute()
    return result.data[0] if result.data else None

def create_demo_account(user_id: str):
    client = get_client()
    if client is None:
        return None
    payload = {"user_id": user_id, "starting_balance": 10000, "balance": 10000, "realized_pnl": 0}
    result = client.table("demo_accounts").insert(payload).execute()
    return result.data[0] if result.data else None

def upsert_demo_account(user_id: str, starting_balance: float, balance: float, realized_pnl: float):
    client = get_client()
    if client is None:
        return None
    payload = {"user_id": user_id, "starting_balance": starting_balance, "balance": balance, "realized_pnl": realized_pnl}
    result = client.table("demo_accounts").upsert(payload, on_conflict="user_id").execute()
    return result.data[0] if result.data else None

def list_paper_trades(user_id: str):
    client = get_client()
    if client is None:
        return []
    result = client.table("paper_trades").select("*").eq("user_id", user_id).order("opened_at", desc=True).execute()
    return result.data or []

def create_paper_trade(user_id: str, trade: dict):
    client = get_client()
    if client is None:
        return None
    result = client.table("paper_trades").insert({**trade, "user_id": user_id}).execute()
    return result.data[0] if result.data else None

def close_paper_trade(user_id: str, trade_id: str, exit_price: float, pnl: float):
    client = get_client()
    if client is None:
        return None
    result = client.table("paper_trades").update({
        "exit": exit_price,
        "pnl": pnl,
        "status": "CLOSED",
        "closed_at": "now()",
    }).eq("id", trade_id).eq("user_id", user_id).eq("status", "OPEN").execute()
    return result.data[0] if result.data else None
