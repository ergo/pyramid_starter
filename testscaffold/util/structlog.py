import structlog


def json_with_extra_processor():
    struct_to_json = structlog.processors.JSONRenderer()

    def attach_extra(logger, name, event_dict):
        msg = struct_to_json(logger, name, event_dict)
        return (msg,), {'extra': event_dict}

    return attach_extra
