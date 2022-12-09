def _serialize(objects, serializer_class):
    serialized = []
    for obj in objects:
        serialized.append(serializer_class(obj).data)
    return serialized

