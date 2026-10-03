#!/usr/bin/env python3
import zmq
from typing import NoReturn

import cereal.messaging as messaging
from cereal.services import SERVICE_LIST
from openpilot.common.logging_extra import SwagLogFileFormatter
from openpilot.system.hardware.hw import Paths
from openpilot.common.swaglog import get_file_handler


def decode_record(data: bytes) -> str:
  return data.decode("utf-8", errors="replace")


def msgq_payload_fits_queue(payload_size: int, queue_size: int) -> bool:
  """Mirror msgq.cc: three aligned messages, including the int64 size tag, must fit."""
  total_msg_size = (int(payload_size) + 8 + 7) & -8
  return 3 * total_msg_size <= int(queue_size)


def main() -> NoReturn:
  log_handler = get_file_handler()
  log_handler.setFormatter(SwagLogFileFormatter(None))
  log_level = 20  # logging.INFO

  ctx = zmq.Context.instance()
  sock = ctx.socket(zmq.PULL)
  sock.bind(Paths.swaglog_ipc())

  # and we publish them
  log_message_sock = messaging.pub_sock('logMessage')
  error_log_message_sock = messaging.pub_sock('errorLogMessage')

  try:
    while True:
      dat = b''.join(sock.recv_multipart())
      level = dat[0]
      record = decode_record(dat[1:])
      if level >= log_level:
        log_handler.emit(record)

      if len(record) > 2*1024*1024:
        print("WARNING: log too big to publish", len(record))
        print(record[:100])
        continue

      # Then publish only payloads that satisfy msgq's native queue-size invariant.
      msg = messaging.new_message(None, valid=True, logMessage=record)
      payload = msg.to_bytes()
      if not msgq_payload_fits_queue(len(payload), SERVICE_LIST["logMessage"].queue_size):
        print("WARNING: log too big for logMessage msgq queue", len(payload))
        continue
      log_message_sock.send(payload)

      if level >= 40:  # logging.ERROR
        msg = messaging.new_message(None, valid=True, errorLogMessage=record)
        payload = msg.to_bytes()
        if msgq_payload_fits_queue(len(payload), SERVICE_LIST["errorLogMessage"].queue_size):
          error_log_message_sock.send(payload)
        else:
          print("WARNING: log too big for errorLogMessage msgq queue", len(payload))
  finally:
    sock.close()
    ctx.term()

    # can hit this if interrupted during a rollover
    try:
      log_handler.close()
    except ValueError:
      pass

if __name__ == "__main__":
  main()
