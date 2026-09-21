from .paper import summary as db_summary, list_trades

def summary():
    return db_summary()

def export_rows():
    return list_trades()
