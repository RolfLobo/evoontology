import json
import threading
from urllib.error import HTTPError
from urllib.request import ProxyHandler, build_opener

import pytest

from evoontology.visualization.preview import serve


def test_preview_serves_only_html_and_expires(tmp_path):
    html = tmp_path / 'ontology.html'
    html.write_text('<h1>ontology</h1>', encoding='utf-8')
    (tmp_path / 'secret.txt').write_text('private', encoding='utf-8')
    thread = threading.Thread(target=serve, args=(html, 'test-token', 0.7), daemon=True)
    thread.start()
    import time
    deadline = time.monotonic() + 3
    state_path = tmp_path / 'preview-server.json'
    while not state_path.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    state = json.loads(state_path.read_text())
    opener = build_opener(ProxyHandler({}))
    with opener.open(state['url']) as response:
        assert response.read() == b'<h1>ontology</h1>'
        assert response.headers['Cache-Control'] == 'no-store'
    for path in ['/secret.txt', '/test-token/../secret.txt', '/wrong/ontology.html']:
        with pytest.raises(HTTPError) as error:
            opener.open(f"http://127.0.0.1:{state['port']}{path}")
        assert error.value.code == 404
    thread.join(3)
    assert not thread.is_alive()
    assert not state_path.exists()
