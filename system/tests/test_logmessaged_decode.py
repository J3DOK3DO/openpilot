from cereal.services import SERVICE_LIST
from openpilot.system import logmessaged


def test_decode_record_replaces_malformed_utf8():
  assert logmessaged.decode_record(b'before\xffafter') == "before\ufffdafter"


def test_msgq_payload_fit_matches_native_three_message_boundary():
  queue_size = SERVICE_LIST["logMessage"].queue_size
  assert queue_size == 256000

  # msgq.cc uses ALIGN(payload_size + sizeof(int64_t)) and requires three
  # complete messages to fit in the queue.
  assert logmessaged.msgq_payload_fits_queue(85320, queue_size)
  assert not logmessaged.msgq_payload_fits_queue(85321, queue_size)
