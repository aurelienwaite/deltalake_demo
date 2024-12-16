from pyspark.sql import SparkSession
from pyspark.sql.functions import window, avg
from delta import configure_spark_with_delta_pip

# Initialize Spark session
builder = (
    SparkSession.builder.appName("Tick Aggregator")
    .config("spark.driver.memory", "8g")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config(
        "spark.sql.catalog.spark_catalog",
        "org.apache.spark.sql.delta.catalog.DeltaCatalog",
    )
)
spark = configure_spark_with_delta_pip(builder).getOrCreate()

# Define the schema of the tick data
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
    TimestampType,
)

tick_schema = StructType(
    [
        StructField("symbol", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("price", DoubleType(), True),
    ]
)

# File source directory (change this to your source directory)
input_path = "./tick_data"

# Read streaming data from the file source
tick_stream = (
    spark.readStream.schema(tick_schema)
    .option("maxFilesPerTrigger", 1)
    .json(input_path)
)  # Assuming tick data is saved as JSON

# Aggregate data over 15 second intervals
aggregated_stream = (
    tick_stream.withWatermark("timestamp", "1 minute")
    .groupBy(window("timestamp", "15 seconds"), "symbol")
    .agg(avg("price").alias("average_price"))
)

# Aggregates can only be written at the table, not row level
# Use this function to write results to a temp table and upsert
# into the main table
def upsertToDelta(microBatchOutputDF, batchId):
  # Set the dataframe to view name
  microBatchOutputDF.createOrReplaceTempView("updates")

  # Use the view name to apply MERGE
  # NOTE: You have to use the SparkSession that has been used to define the `updates` dataframe

  microBatchOutputDF.sparkSession.sql("""
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
delta_lake_stream = (
    aggregated_stream.selectExpr("symbol", "window as timeslice", "average_price")
    .writeStream
    .foreachBatch(upsertToDelta)
    .outputMode("update")
    .start()
)

delta_lake_stream.awaitTermination()
