"""Service-level errors mapped to the frozen error contract. Messages are safe for clients."""


class ServiceError(Exception):
    def __init__(self, status: int, code: str, message: str, retryable: bool, action: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message
        self.retryable, self.action = retryable, action


def engine_unavailable(reason: str) -> ServiceError:
    return ServiceError(503, "INTERNAL_ERROR", "Image generation is not available on this server.",
                        False, reason)


def model_load_failed() -> ServiceError:
    return ServiceError(500, "INTERNAL_ERROR", "The image model could not be loaded.", True,
                        "Retry later; if it keeps failing, check the server logs.")


def out_of_memory() -> ServiceError:
    return ServiceError(503, "RESOURCE_EXHAUSTED", "The server ran out of memory for this request.",
                        True, "Retry with a lower resolution or the quick quality mode.")


def busy() -> ServiceError:
    return ServiceError(429, "RESOURCE_EXHAUSTED", "Another image is being generated right now.",
                        True, "Retry in a few seconds.")


def unsupported_resolution(supported: tuple[int, ...]) -> ServiceError:
    return ServiceError(422, "INVALID_REQUEST", "Requested resolution is not supported.", False,
                        "Use one of: " + ", ".join(str(r) for r in supported))


def no_safe_configuration(message: str, action: str) -> ServiceError:
    """P6: the adaptive controller found no profiled configuration that fits the available resources."""
    return ServiceError(503, "RESOURCE_EXHAUSTED", message, True, action)
