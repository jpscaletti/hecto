from hecto.utils import JinjaRender

from ..helpers import PROJECT_TEMPLATE, DATA


def test_render(dst):
    envops = {}
    envops.setdefault("block_start_string", "[%")
    envops.setdefault("block_end_string", "%]")
    envops.setdefault("variable_start_string", "[[")
    envops.setdefault("variable_end_string", "]]")

    render = JinjaRender(PROJECT_TEMPLATE, DATA, envops)

    assert render.string("/hello/[[ what ]]/") == "/hello/world/"
    assert render.string("/hello/world/") == "/hello/world/"
