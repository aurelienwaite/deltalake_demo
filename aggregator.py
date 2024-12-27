from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
    TimestampType,
)
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import window, avg
import pyarrow as pa
import pyarrow.flight as flight
from datetime import datetime
from pyspark.sql.functions import udf
import pandas as pd
import pyspark
from dateutil import parser

# Initialize Spark session
spark = (
    SparkSession.builder.appName("Tick Aggregator")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config(
        "spark.sql.catalog.spark_catalog",
        "org.apache.spark.sql.delta.catalog.DeltaCatalog"
    )
    .config(
        "spark.sql.streaming.stateStore.providerClass",
        "org.apache.spark.sql.execution.streaming.state.RocksDBStateStoreProvider"
    )
    .config(
        "spark.databricks.streaming.statefulOperator.asyncCheckpoint.enabled",
        "true"
    )
    .config(
        "spark.sql.shuffle.partitions",
        "1"
    )
    .config(
        "spark.sql.streaming.statefulOperator.stateRebalancing.enabled",
        "true",
    )
    .getOrCreate()
)

# Define the schema of the tick data

tick_schema = StructType(
    [
        StructField("symbol", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("price", DoubleType(), True),
    ]
)

#raw_schema = StructType([StructField("value", tick_schema)])

arrow_schema = pa.schema([
    pa.field("symbol", pa.string()),
    pa.field("timestamp", pa.timestamp('ns', tz='UTC')),
    pa.field("price", pa.float64())
])

# File source directory (change this to your source directory)
input_path = "/aggregator/tick_data"

# Read streaming data from the file source
kafka_stream: DataFrame = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "172.17.0.1:9092")
    .option("subscribe", "ticks") \
    # .schema(tick_schema)
    .load()
)


def deserialize_arrow_message(binary_message):
    reader = pa.ipc.open_stream(binary_message)
    table = reader.read_all().cast(arrow_schema)
    as_dict = table.to_pydict()
    row = {key: value[0] for key, value in as_dict.items()}
    return row


deserialize_udf = udf(deserialize_arrow_message, tick_schema, useArrow=True)

raw_stream = kafka_stream.selectExpr("CAST(value AS BINARY)")
tick_stream = raw_stream.withColumn("nested", deserialize_udf(raw_stream["value"])).selectExpr(
    "nested.symbol as symbol", "nested.timestamp as timestamp", "nested.price as price")

# Aggregate data over 15 second intervals
aggregated_stream: DataFrame = (
    tick_stream.withWatermark("timestamp", "1 milliseconds")
    .groupBy(window("timestamp", "1 seconds"), "symbol")
    .agg(avg("price").alias("average_price"))
    .selectExpr("symbol", "window as timeslice", "average_price")
)
aggregated_stream_schema = aggregated_stream.schema

def write_arrow(batches: list):
    batches_as_list = list(batches)
    print("Hullo")

    if batches_as_list:
        alpha_client = flight.FlightClient("grpc://172.17.0.1:8815")
        descriptor = flight.FlightDescriptor.for_path("aggregated_ticks")
        table = pa.Table.from_batches(batches_as_list)
        writer, _ = alpha_client.do_put(descriptor, table.schema)
        writer.write_table(table)
        writer.close()
    else:
        print("No batches to write")

    return []


def send_to_alpha(batch_df: DataFrame, batchId: int):
    batch_df.mapInArrow(write_arrow, schema=aggregated_stream_schema).collect()
    return batch_df


alpha_stream = (
    aggregated_stream
    .writeStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "host1:port1,host2:port2")
    .option("topic", "aggregat")
    .outputMode("append")
    .start()
)

# Aggregates can only be written at the table, not row level
# Use this function to write results to a temp table and upsert
# into the main table


def upsert_to_delta(batch_df: DataFrame, batchId: int):
    # Set the dataframe to view name
    batch_df.createOrReplaceTempView("updates")

    # Use the view name to apply MERGE
    # NOTE: You have to use the SparkSession that has been used to define the `updates` dataframe
    batch_df.sparkSession.sql("""
    MERGE INTO delta_lake_table t
    USING updates s
    ON s.symbol = t.symbol AND s.timeslice = t.timeslice
    WHEN MATCHED THEN UPDATE SET *
    WHEN NOT MATCHED THEN INSERT *
  """)


# Create the main table
spark.sql("""
  CREATE TABLE delta_lake_table (symbol STRING, timeslice STRUCT<start: TIMESTAMP, end: TIMESTAMP>, average_price FLOAT) USING delta
""")

# Write results
"""delta_lake_stream = (
    aggregated_stream.selectExpr(
        "symbol", "window as timeslice", "average_price")
    .writeStream
    .foreachBatch(upsert_to_delta)
    .outputMode("update")
    .start()
)

delta_lake_stream.awaitTermination()"""
alpha_stream.awaitTermination()
