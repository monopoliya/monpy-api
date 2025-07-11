import logging

message_format = ('[%(asctime)s] [%(levelname)s] '
                  '[%(filename)s:%(lineno)d] :: %(message)s')

logging.basicConfig(
    level=logging.INFO,
    format=message_format,
    datefmt='%d.%m.%Y %H:%M:%S'
)


def get_logger(name: str):
    return logging.getLogger(name)
