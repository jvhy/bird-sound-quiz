import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def get_retry_request_session(retries: int = 5) -> requests.Session:
    """
    Creates a request session that retries failed requests.

    :param retries: Maximum number of retries for a request.
    :returns session: Request session with retry strategy.
    """

    retry_strategy = Retry(
        total=retries,
        status_forcelist=[408, 429, 500, 502, 503, 504],
        backoff_factor=2
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session
