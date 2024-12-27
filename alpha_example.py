import pyarrow as pa
import pyarrow.flight as flight
import polars as pl
from datetime import datetime, timezone


def do_compute(arrow_table):
    df = pl.from_arrow(arrow_table)
    processing_time: datetime = df.select(pl.col("timeslice")).unnest(
        "timeslice").select(pl.max("end")).rows()[0][0]
    print(f"Latency = {(datetime.now(tz=timezone.utc) - processing_time).total_seconds() *1000} millis")

class FlightServer(flight.FlightServerBase):
    def __init__(self, host="0.0.0.0", port=8815):
        super().__init__(location=f"grpc://{host}:{port}")
        print(f"Flight server running on {host}:{port}")

    def do_put(self, context, descriptor, reader, writer):
        # Read the Arrow table from the client
        start = datetime.now()
        table = reader.read_all()
        do_compute(table)
        end = datetime.now()
        print(f"Marshalling took {(end - start).total_seconds()} seconds")

    def list_flights(self, context, criteria):
        # Optionally list available flights (not needed for simple servers)
        return iter([])


if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8815

    server = FlightServer(host, port)
    try:
        server.serve()
    except KeyboardInterrupt:
        print("Server shutting down.")
