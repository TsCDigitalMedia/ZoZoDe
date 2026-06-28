from zozode.cli import build_parser


def test_zozode_defaults_to_server_mode():
    args = build_parser().parse_args([])

    assert args.join is None
    assert args.port == 2806


def test_zozode_join_sets_client_host():
    args = build_parser().parse_args(['--join', '192.168.1.10'])

    assert args.join == '192.168.1.10'
    assert args.port == 2806
