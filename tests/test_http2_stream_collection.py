"""HTTP negotiation is recorded and config changes do not alter requests."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('http2_transport_test', ROOT/'scripts/97_http2_stream_collection.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


class Http2TransportTests(unittest.TestCase):
    def test_only_protocol_line_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'fixture.curl'
            before = 'url = "https://example.invalid"\nsilent\nhttp1.1\nno-buffer\n'
            path.write_text(before)
            h.set_http2(path)
            self.assertEqual(path.read_text(), before.replace('\nhttp1.1\n', '\nhttp2\n'))

    def test_last_http_status_block_controls_negotiated_version(self):
        self.assertEqual(h.response_http_version('HTTP/1.1 200 Connection established\n\nHTTP/2 200\n'), '2')
        self.assertEqual(h.response_http_version('HTTP/1.1 200 OK\n'), '1.1')
        self.assertIsNone(h.response_http_version('incomplete'))


if __name__ == '__main__': unittest.main()
