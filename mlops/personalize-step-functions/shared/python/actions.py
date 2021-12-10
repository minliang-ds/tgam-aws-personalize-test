class ResourcePending(Exception):
    pass


class ResourceFailed(Exception):
    pass


def take_action(status):
    if status in {'CREATE PENDING', 'CREATE IN_PROGRESS', 'RUNNING'}:
        raise ResourcePending
    if status not in {'ACTIVE', 'SUCCEEDED'}:
        raise ResourceFailed
    return True


def take_action_delete(status):
    if status in {'DELETE PENDING', 'DELETE IN_PROGRESS'}:
        raise ResourcePending
    raise ResourceFailed
