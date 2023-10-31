from jsonrpc import Dispatcher
from jsonrpc.backend.django import JSONRPCAPI

api = JSONRPCAPI(dispatcher=Dispatcher())


@api.dispatcher.add_method
def my_method(request, *args, **kwargs):
    print(request)
    return args, kwargs
