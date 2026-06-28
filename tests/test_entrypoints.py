from zozode.client import build_parser as build_client_parser
from zozode.server import build_parser as build_server_parser


def test_client_defaults_to_message_for_simple_run():
    args = build_client_parser().parse_args([])

    assert args.message == "hello from ZoZoDe"
    assert args.host == "127.0.0.1"
    assert args.port == 2806


def test_server_defaults_to_localhost_port():
    args = build_server_parser().parse_args([])

    assert args.host == "127.0.0.1"
    assert args.port == 2806
