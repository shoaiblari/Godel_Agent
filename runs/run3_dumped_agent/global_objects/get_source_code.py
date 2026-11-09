

def get_source_code(obj, obj_name):
    if hasattr(obj, '__source__'):
        if inspect.isclass(obj):
            return f'class {obj_name}:\n' + "\n\n".join(f"{code}" for code in obj.__source__.values())
        return obj.__source__
    else:
        return inspect.getsource(obj)
