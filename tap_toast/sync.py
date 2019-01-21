import json

import singer
import singer.metrics as metrics
from singer import metadata
from singer import Transformer

LOGGER = singer.get_logger()


def sync_stream(state, instance):
    stream = instance.stream

    # If we have a bookmark, use it; otherwise use start_date
    # if (instance.replication_method == 'INCREMENTAL' and
    #         not state.get('bookmarks', {}).get(stream.tap_stream_id, {}).get(instance.replication_key)):
    #     singer.write_bookmark(state,
    #                           stream.tap_stream_id,
    #                           instance.replication_key)

    with metrics.record_counter(stream.tap_stream_id) as counter:
        for (stream, record) in instance.sync(state):
            counter.increment()

            # SCHEMA_GEN: Comment out transform
            with Transformer() as transformer:
                record = transformer.transform(record, stream.schema.to_dict(), metadata.to_map(stream.metadata))

            singer.write_record(stream.tap_stream_id, record)
            # NB: We will only write state at the end of a stream's sync:
            #  We may find out that there exists a sync that takes too long and can never emit a bookmark
            #  but we don't know if we can guarentee the order of emitted records.

        if instance.replication_method == "INCREMENTAL":
            singer.write_state(state)

        return counter.value
