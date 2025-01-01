import pathway as pw
import pyarrow as pa
from beartype.typing import Tuple, List
from datetime import timedelta, datetime

TICK_TOPIC = "tick"
AGG_TOPIC = "aggregate"

arrow_schema = pa.schema([
    pa.field("symbol", pa.string()),
    pa.field("timestamp", pa.timestamp('ns', tz='UTC')),
    pa.field("price", pa.float64())
])

def parse_arrow(binary_message: bytes) -> List[Tuple[str, pw.DateTimeUtc, float]]:
    reader = pa.ipc.open_stream(binary_message)
    table = reader.read_all().cast(arrow_schema)
    columns = [table[column] for column in ["symbol", "timestamp", "price"]]
    as_py = []
    for row_idx in range(table.num_rows):
        row = [column[row_idx].as_py() for column in columns]
        as_py.append(row)
    return as_py


def dataflow(raw_ticks: pw.Table) -> pw.Table:

    parsed_arrow = raw_ticks.select(
        data=pw.udf(parse_arrow, deterministic=True)(pw.this.data),
    )
    flattened = parsed_arrow.flatten(parsed_arrow.data)
    ticks = flattened.select(
        symbol=flattened.data[0], timestamp=flattened.data[1], price=flattened.data[2])

    agg = ticks.windowby(
        ticks.timestamp,
        window=pw.temporal.tumbling(duration=timedelta(seconds=1)),
        instance=ticks.symbol,
        behavior=pw.temporal.common_behavior(cutoff=timedelta(seconds=10), keep_results=False)
    ).reduce(
        symbol=pw.this._pw_instance,
        start=pw.this._pw_window_start,
        end=pw.this._pw_window_end,
        sum=pw.reducers.sum(pw.this.price),
        count=pw.reducers.count(),
    )

    def agg_to_arrow(symbol: str, start: datetime, end: datetime, sum: float, count: float) -> bytes:
        table = pa.table({
            "symbol": pa.array([symbol], type=pa.string()),
            "start": pa.array([start], type=pa.timestamp('us', tz='UTC')),
            "end": pa.array([end], type=pa.timestamp('us', tz='UTC')),
            "sum": pa.array([sum], type=pa.float64()),
            "count": pa.array([count], type=pa.float64())
        })
        
        sink = pa.BufferOutputStream()
        writer = pa.ipc.new_stream(sink, table.schema)
        writer.write_table(table)
        writer.close()
        buffer = sink.getvalue()
        return buffer.to_pybytes()

    agg_arrow = agg.select(
        data=pw.udf(agg_to_arrow, deterministic=True)(pw.this.symbol, pw.this.start, pw.this.end, pw.this.sum, pw.this.count),
    )
    return agg_arrow

