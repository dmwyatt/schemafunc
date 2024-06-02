class NoDocstringError(Exception):
    pass


class ParameterNotDocumentedError(Exception):
    pass


class ParameterMissingDescriptionError(Exception):
    pass


class NoShortDescriptionError(Exception):
    pass


class UnsupportedTypeError(Exception):
    pass


class BareGenericTypeError(ValueError):
    pass


class UnsupportedLiteralTypeError(Exception):
    pass
