"""A basic test case for client API usage extraction."""

import os
import pandas as pd
from collections import deque, defaultdict
from sys import exit as z

if __name__ == "__main__":
    os.mkdir("test")
    df = pd.read_csv("test.csv")
    df = pd.DataFrame()
    df.head(10)
    x = deque(["a", "b", "c"])
    x.append("d")
    y = defaultdict()
    y["a"] = "b"
    z(0)
