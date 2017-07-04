import logging

import structlog
from aiohttp import web

from disk_usage_exporter.context import Context
from disk_usage_exporter.exporter import get_app
from disk_usage_exporter.logging import configure_logging

_logger = structlog.get_logger()


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(
        description='prometheus disk usage metrics exporter'
    )

    parser.add_argument(
        '--listen-host',
        help='Interface to listen on',
    )
    parser.add_argument(
        '--listen-port',
        help='Port number to listen on',
        default=9274,
        type=int,
    )

    parser.add_argument(
        '--log-level',
        help='Log level',
        default='INFO',
    )
    parser.add_argument(
        '--log-human',
        action='store_true',
        help='Emit logging messages for humans. Messages are emitted as JSON '
             'lines by default',
    )

    args = parser.parse_args(args=argv)

    configure_logging(
        for_humans=args.log_human,
        level=getattr(logging, args.log_level)
    )

    context = Context(export_all_mounts=args.export_all_mounts)

    web.run_app(
        get_app(context),
        host=args.listen_host,
        port=args.listen_port,
        access_log=structlog.get_logger(f'{__package__}.access_log'),
        print=lambda x: _logger.info('run_app.print', message=x),
    )


if __name__ == '__main__':
    main()
