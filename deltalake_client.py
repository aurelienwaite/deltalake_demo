# Demo of reading the data lake

import polars as pl

ticks_df = pl.read_delta("./spark_home/delta_lake_table", use_pyarrow=True)
print(ticks_df.describe())