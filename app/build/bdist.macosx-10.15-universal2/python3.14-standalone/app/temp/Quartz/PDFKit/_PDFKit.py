def __load():
    import os, sys, importlib.machinery, importlib._bootstrap
    ext = 'Quartz/PDFKit/_PDFKit.so'
    for path in sys.path:
        if not path.endswith('lib-dynload'):
            continue
        ext_path = os.path.join(path, ext)
        if os.path.exists(ext_path):
            loader = importlib.machinery.ExtensionFileLoader(
                 __name__, ext_path)
            spec = importlib.machinery.ModuleSpec(
                name=__name__, loader=loader, origin=ext_path)
            importlib._bootstrap._load(spec)
            break
    else:
        raise ImportError(repr(ext) + " not found")
__load()
del __load
