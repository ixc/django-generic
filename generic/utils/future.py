from django import urls

def resolve_url(to, *args, **kwargs):
    """
    Return a URL appropriate for the arguments passed.

    The arguments could be:

        * A model: the model's `get_absolute_url()` function will be called.

        * A view name, possibly with arguments: `urls.reverse()` will
          be used to reverse-resolve the name.

        * A URL, which will be returned as-is.

    """
    # If it's a model, use get_absolute_url()
    if hasattr(to, 'get_absolute_url'):
        return to.get_absolute_url()

    # Next try a reverse URL resolution.
    try:
        return urls.reverse(to, args=args, kwargs=kwargs)
    except urls.NoReverseMatch:
        # If this is a callable, re-raise.
        if callable(to):
            raise
        # If this doesn't "feel" like a URL, re-raise.
        if '/' not in to and '.' not in to:
            raise

    # Finally, fall back and assume it's a URL
    return to
