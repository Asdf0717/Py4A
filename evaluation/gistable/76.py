import zipimport

# Used to try and prevent bugs from people who see that Wheels
# support being added to sys.path and expect that your library/tool should
# support this misfeature.
try:
    if isinstance(__loader__, zipimport.zipimporter):
        raise RuntimeError(
            "Zipped imports are not supported, use something less terrible."
        )
except NameError:
    pass
