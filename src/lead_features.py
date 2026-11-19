import pandas as pd


def add_shortage(df):
    df = pd.DataFrame(df).copy()
    df["shortage"] = (df["quantity_ordered"] - df["stock_at_acceptance"]).clip(lower=0)
    return df
