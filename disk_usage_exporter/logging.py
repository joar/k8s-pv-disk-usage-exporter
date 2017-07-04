import logging
import logging.config
import sys
from typing import Dict, Any, Optional, List

import attr
import structlog


class Loggable:
    def __structlog__(self):
        if attr.has(type(self)):
            return attr.asdict(self)
        return self


def add_message(logger, method_name, event_dict):
    """
    Creates a ``message`` value based on the ``hint`` and ``key_hint`` keys.

    ``key_hint`` : ``Optional[str]``
        a '.'-separated path of dictionary keys.

    ``hint`` : ``Optional[str]``
        will be formatted using ``.format(**event_dict)``.
    """
    def from_hint(ed):
        hint = event_dict.pop('hint', None)
        if hint is None:
            return

        try:
            return hint.format(**event_dict)
        except Exception as exc:
            return f'! error formatting message: {exc!r}'

    def path_value(dict_: Dict[str, Any], key_path: str) -> Optional[Any]:
        value = dict_

        for key in key_path.split('.'):
            if value is None:
                return
            if hasattr(value, '__structlog__'):
                value = value.__structlog__()
            value = value.get(key)

        return value

    def from_key_hint(ed) -> Optional[str]:
        key_hint = ed.pop('key_hint', None)
        if key_hint is None:
            return

        value = path_value(ed, key_hint)

        return f'{key_hint}={value!r}'

    def from_key_hints(ed) -> List[str]:
        key_hints = ed.pop('key_hints', None)
        if key_hints is None:
            return []

        return [
            f'{key_hint}={path_value(ed, key_hint)!r}'
            for key_hint in key_hints
        ]

    hints = [
        from_hint(event_dict),
        from_key_hint(event_dict)
    ]
    hints += from_key_hints(event_dict)

    if all(hint is None for hint in hints):
        return event_dict

    prefix = event_dict['event']
    hint = ', '.join(hint for hint in hints if hint is not None)

    message = event_dict.get('message')
    if message is not None:
        message = f'{prefix}: {message}, {hint}'
    else:
        message = f'{prefix}: {hint}'

    event_dict['message'] = message
    return event_dict


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
    foreign_pre_chain = [
        # Add the log level and a timestamp to the event_dict if the log entry
        # is not from structlog.
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.add_log_level,
        timestamper,
    ]
    if for_humans:
        foreign_pre_chain += [
            structlog.processors.format_exc_info,
        ]

    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        add_severity,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        timestamper,
        add_message,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'structlog': {
                '()': structlog.stdlib.ProcessorFormatter,
                'processor': renderer,
                'foreign_pre_chain': foreign_pre_chain,
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
