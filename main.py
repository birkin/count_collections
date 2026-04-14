import argparse
import logging
import os
import pprint
import sys

import httpx

DEFAULT_API_URL = 'https://repository.library.brown.edu/api/search/'
DEFAULT_QUERY = 'object_type:bdr-collection'
DEFAULT_TIMEOUT_SECONDS = 30.0

## basic logging ---------------------------------------------------

"""
From a `main.py` file, somewhere near the top.
- Shows the logging `format` I really like.
- Shows a clean way to default the log-level to INFO if LOG_LEVEL is not `DEBUG`.
- Shows optional file-logging.
"""

# log_dir: Path = stuff_dir / 'logs'
# log_dir.mkdir(parents=True, exist_ok=True)  # creates the log-directory inside the stuff-directory if it doesn't exist
# log_file_path: Path = log_dir / 'auto_updater.log'
logging.basicConfig(
    level=logging.DEBUG if os.getenv('LOG_LEVEL') == 'DEBUG' else logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s',
    datefmt='%d/%b/%Y %H:%M:%S',
    # filename=log_file_path,
)
log = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """
    Builds the command-line parser.

    Called by: main()
    """
    parser = argparse.ArgumentParser(description='Returns the number of public collections in the BDR.')
    parser.add_argument(
        '--api-url',
        default=DEFAULT_API_URL,
        help='BDR search API URL. Default: %(default)s',
    )
    parser.add_argument(
        '--query',
        default=DEFAULT_QUERY,
        help='Solr query used to identify collections. Default: %(default)s',
    )
    parser.add_argument(
        '--timeout',
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help='HTTP timeout in seconds. Default: %(default)s',
    )
    return parser


def fetch_collection_count(api_url: str, query: str, timeout: float) -> int:
    """
    Fetches the collection count from the public BDR search API.

    Called by: main()
    """
    log.debug(f'Fetching collection count from ``{api_url}`` with query ``{query}``')

    params = {
        'q': query,
        'rows': 0,
        'fl': 'pid',
    }

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(api_url, params=params)
        response.raise_for_status()
        payload = response.json()

    response_data = payload.get('response')
    if not isinstance(response_data, dict):
        raise ValueError('API response is missing a top-level "response" object.')
    log.debug(f'response, ``{pprint.pformat(response_data)}``')

    num_found = response_data.get('numFound')
    if not isinstance(num_found, int):
        raise ValueError('API response is missing an integer "response.numFound" value.')

    return num_found


def main() -> None:
    """
    Parses arguments, fetches the BDR collection count, and prints it.

    Called by: __main__
    """
    parser = build_parser()
    args = parser.parse_args()

    try:
        collection_count = fetch_collection_count(args.api_url, args.query, args.timeout)
    except (httpx.HTTPError, ValueError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        raise SystemExit(1) from exc

    print(collection_count)


if __name__ == '__main__':
    main()
