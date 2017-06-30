import sys
import logging
import logging.config
from pathlib import Path

import structlog
from aiohttp import web

from disk_usage_exporter.exporter import get_app
from disk_usage_exporter.context import Context

_logger = structlog.get_logger()


def add_severity(logger, method_name, event_dict):
    event_dict = structlog.stdlib.add_log_level(logger, method_name, event_dict)
    level = event_dict.pop('level')

    if level is not None:
        event_dict['severity'] = level.upper()

    return event_dict


def configure_logging(for_humans=False, level=logging.INFO):
    if not for_humans:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(
            colors=structlog.dev._has_colorama
        )

    timestamper = structlog.processors.TimeStamper(fmt='%Y-%m-%d %H:%M:%S')
    pre_chain = [
        # Add the log level and a timestamp to the event_dict if the log entry
        # is not from structlog.
        structlog.stdlib.add_log_level,
        timestamper,
    ]
    if for_humans:
        pre_chain += [
            structlog.processors.format_exc_info,
        ]

    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        add_severity,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt='%Y-%m-%d %H:%M.%S', utc=False),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'structlog': {
                '()': structlog.stdlib.ProcessorFormatter,
                'processor': renderer,
                'foreign_pre_chain': pre_chain,
            },
        },
        'handlers': {
            'default': {
                'level': level,
                'class': 'logging.StreamHandler',
                'stream': sys.stdout,
                'formatter': 'structlog',
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': 'DEBUG',
                'propagate': True,
            },
        }
    })

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


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
        '--export-all-mounts',
        help='Export metrics for all mounts. Defaults to export only PV mounts',
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
