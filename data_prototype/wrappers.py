from matplotlib.lines import Line2D as _Line2D


class ProxyWrapper:
    _privtized_methods = ()
    _wrapped_class = None
    _wrapped_instance = None
    data = None

    def draw(self, renderer):
        raise NotImplementedError

    def __getattr__(self, key):
        if key in self._privtized_methods:
            raise AttributeError(f"The method {key} has been privitized")
        if key[0] == "_" and key[1:] in self._privtized_methods:
            return getattr(self._wrapped_instance, key[1:])
        return getattr(self._wrapped_instance, key)

    def __setattr__(self, key, value):
        if hasattr(self._wrapped_instance, key):
            setattr(self._wrapped_instance, key, value)
        else:
            super().__setattr__(key, value)

    def _query_and_transform(self, renderer):
        ax = self._wrapped_instance.axes
        ax_bbox = ax.get_window_extent(renderer)
        return {
            # doing this here is nice because we can write it once, but we really want to
            # push this computation down a layer
            k: self.nus.get(k, lambda x: x)(v)
            for k, v in self.data.query([*ax.get_xlim(), *ax.get_ylim()], ax_bbox.size).items()
        }

    def __init__(self, data, nus):
        self.data = data
        self.nus = nus or {}


class LineWrapper(ProxyWrapper):
    _wrapped_class = _Line2D
    _privtized_methods = set(["set_xdata", "set_ydata", "set_data"])

    def __init__(self, data, nus=None, /, **kwargs):
        super().__init__(data, nus)
        self._wrapped_instance = self._wrapped_class([], [], **kwargs)

    def draw(self, renderer):
        data = self._query_and_transform(renderer)
        self._wrapped_instance.set_data(data["x"], data["y"])
        return self._wrapped_instance.draw(renderer)
