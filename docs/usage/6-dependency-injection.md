# Dependency Injection

Starlite has a simple but powerful dependency injection system. To explain how it works lets begin with 4 different
functions, each returning a different kind of value:

```python
def bool_fn() -> bool:
    ...


def dict_fn() -> dict:
    ...


def list_fn() -> list:
    ...


def int_fn() -> int:
    ...
```

We can declare dependencies on different levels of the application using the `Provide` class:

```python
from starlite import Controller, Router, Starlite, Provide, get

from my_app.dependencies import bool_fn, dict_fn, int_fn, list_fn


class MyController(Controller):
    path = "/controller"
    # on the controller
    dependencies = {"controller_dependency": Provide(list_fn)}

    # on the route handler
    @get(path="/handler", dependencies={"local_dependency": Provide(int_fn)})
    def my_route_handler(
        self,
        app_dependency: bool,
        router_dependency: dict,
        controller_dependency: list,
        local_dependency: int,
    ) -> None:
        ...

    # on the router


my_router = Router(
    path="/router",
    dependencies={"router_dependency": Provide(dict_fn)},
    route_handlers=[MyController],
)

# on the app
app = Starlite(
    route_handlers=[my_router], dependencies={"app_dependency": Provide(bool_fn)}
)
```

In the above example, the route handler function `my_route_handler` has four different dependencies injected into it as
kwargs.

## Pre-requisites and Scope

The pre-requisites for dependency injection are these:

1. dependencies must be callables (sync or async).
2. dependencies can receive kwargs and a `self` arg but not other args.
3. the kwarg name and the dependency key must be identical.
4. the dependency must be declared using the `Provide` class.
5. the dependency must be in the _scope_ of the handler function.

What is _scope_ in this context? Dependencies are **isolated** to the context in which they are declared. Thus, in the
above example, the `local_dependency` can only be accessed within the specific route handler on which it was declared;
The `controller_dependency` is available only for route handlers on that specific controller; And the router
dependencies are available only to the route handlers registered on that particular router. Only the `app_dependencies`
are available to all route handlers.

## Dependency Kwargs

As stated above dependencies can receive kwargs but no args. The reason for this is that dependencies are parsed using
the same mechanism that parses route handler functions, and they too - like route handler functions, can have data
injected into them.

In fact, you can inject the same data that you
can [inject into route handlers](2-route-handlers.md#handler-function-kwargs) except other dependencies.

Let's say we have a model called `Wallet`, which we'll assume we persist in a DB:

```python title="my_app/models.py"
from pydantic import BaseModel, UUID4

class Wallet(BaseModel):
    id: UUID4
    currency: str
    value: float
```

We have a `WalletController` class with basic CRUD route handlers:

```python title="my_app/wallet/controller.py"
from starlite import Controller, Partial, delete, get, patch, post

from my_app.models import Wallet


class WalletController(Controller):
    path = "/wallet"

    @post()
    async def create_wallet(self, data: Wallet) -> Wallet:
        ...

    @get(path="/{wallet_id:uuid}")
    async def retrieve_wallet(self, wallet: Wallet) -> Wallet:
        ...

    @patch(path="/{wallet_id:uuid}")
    async def update_wallet(self, data: Partial[Wallet], wallet: Wallet) -> Wallet:
        ...

    @delete(path="/{wallet_id:uuid}")
    async def delete_wallet(self, wallet: Wallet) -> None:
        ...
```

We need to inject the wallet instance into the `retrieve_wallet`, `update_wallet` and `delete_wallet` routes. To do
this we will create a dependency that takes a `wallet_id` kwarg and then retrieves the instance from the DB:

```python title="my_app/dependencies.py"
from pydantic import UUID4

from my_app.models import Wallet


async def get_wallet_by_id(wallet_id: UUID4) -> Wallet:
    ...
```

We will now set it on the controller with the correct keyword:


```python title="my_app/wallet/controller.py"
from starlite import Controller, Provide

from my_app.dependencies import get_wallet_by_id


class WalletController(Controller):
    path = "/wallet"
    dependencies = { "wallet": Provide(get_wallet_by_id) }

    # ...
```

This is it - since the controller methods declared the correct path parameter, this value will be passed into
the `get_wallet_by_id`.

## Overriding Dependencies

Because dependencies are declared at each level using a string keyed dictionary, overriding dependencies is very simple:

```python
from starlite import Controller, Provide, get

from my_app.dependencies import bool_fn, dict_fn


class MyController(Controller):
    path = "/controller"
    # on the controller
    dependencies = {"some_dependency": Provide(dict_fn)}

    # on the route handler
    @get(path="/handler", dependencies={"some_dependency": Provide(bool_fn)})
    def my_route_handler(
        self,
        some_dependency: bool,
    ) -> None:
        ...
```

As you can see in the above - the lower scoped route handler function declares a dependency with the same key as the one
declared on the higher scoped controller. The lower scoped dependency therefore overrides the higher scoped one. This
logic applies on all layers.

## The Provide Class

`Provide` is a simple wrapper that takes a callable as a required arg, and an optional kwarg - `use_cache`.

By default `Provide` will not cache the return value of the dependency, and it will be executed on every call to
the route handler that uses it. If `use_cache` is `True`, it will cache the return value on the first execution and
will not call it again.

!!! important
    The caching done inside `Provide` is very simple - it stores the return value and returns it.
    There is no sophisticated comparison of kwargs, LRU implementation etc. so you should be careful when
    you choose to use this option.
