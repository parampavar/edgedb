#
# This source file is part of the EdgeDB open source project.
#
# Copyright 2008-present MagicStack Inc. and the EdgeDB authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from __future__ import annotations

from typing import (
    Any,
    Optional,
    ContextManager,
    Self,
)

import collections
import re


class ContextLevel:
    _stack: CompilerContext[Self]

    def __init__(self, prevlevel: Optional[Self], mode: Any) -> None:
        pass

    def on_pop(
        self: Self,
        prevlevel: Optional[Self],
    ) -> None:
        pass

    def new(
        self: Self,
        mode: Any=None,
    ) -> CompilerContextManager[Self]:
        return self._stack.new(mode, self)

    def reenter(
        self: Self,
    ) -> CompilerReentryContextManager[Self]:
        return CompilerReentryContextManager(self._stack, self)


class CompilerContextManager[ContextLevel_T: ContextLevel](
    ContextManager[ContextLevel_T]
):
    def __init__(
        self,
        context: CompilerContext[ContextLevel_T],
        mode: Any,
        prevlevel: Optional[ContextLevel_T],
    ) -> None:
        self.context = context
        self.mode = mode
        self.prevlevel = prevlevel

    def __enter__(self) -> ContextLevel_T:
        return self.context.push(self.mode, self.prevlevel)

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.context.pop()


class CompilerReentryContextManager[ContextLevel_T: ContextLevel](
    ContextManager[ContextLevel_T]
):
    def __init__(
        self,
        context: CompilerContext[ContextLevel_T],
        level: ContextLevel_T,
    ) -> None:
        self.context = context
        self.level = level

    def __enter__(self) -> ContextLevel_T:
        return self.context._push(None, initial=self.level)

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.context.pop()


class CompilerContext[ContextLevel_T: ContextLevel]:
    stack: list[ContextLevel_T]
    ContextLevelClass: type[ContextLevel_T]
    default_mode: Any

    def __init__(self, initial: ContextLevel_T) -> None:
        self.stack = []
        self._push(None, initial=initial)

    def push(
        self,
        mode: Any,
        prevlevel: Optional[ContextLevel_T] = None,
    ) -> ContextLevel_T:
        return self._push(mode, prevlevel)

    def _push(
        self,
        mode: Any,
        prevlevel: Optional[ContextLevel_T] = None,
        *,
        initial: Optional[ContextLevel_T] = None,
    ) -> ContextLevel_T:
        if initial is not None:
            level = initial
        else:
            if prevlevel is None:
                prevlevel = self.current
            elif prevlevel is not self.current:
                # In the past, we always used self.current as the
                # previous level and simply ignored the prevlevel
                # parameter. Actually using prevlevel makes more sense
                # and has fewer gotchas, but enough code had grown to
                # depend on the old behavior that changing it required
                # asserting that they were the same.  We can consider
                # dropping the assertion if it proves tedious.
                raise AssertionError(
                    'Calling new() on a context other than the current one')
            level = self.ContextLevelClass(prevlevel, mode)
        level._stack = self
        self.stack.append(level)
        return level

    def pop(self) -> None:
        level = self.stack.pop()
        level.on_pop(self.stack[-1] if self.stack else None)

    def new(
        self,
        mode: Any = None,
        prevlevel: Optional[ContextLevel_T] = None,
    ) -> CompilerContextManager[ContextLevel_T]:
        if mode is None:
            mode = self.default_mode
        return CompilerContextManager(self, mode, prevlevel)

    @property
    def current(self) -> ContextLevel_T:
        return self.stack[-1]


class SimpleCounter:
    counts: collections.defaultdict[str, int]

    def __init__(self) -> None:
        self.counts = collections.defaultdict(int)

    def nextval(self, name: str = 'default') -> int:
        self.counts[name] += 1
        return self.counts[name]


class AliasGenerator(SimpleCounter):
    def get(self, hint: str = '') -> str:
        if not hint:
            hint = 'v'
        m = re.search(r'~\d+$', hint)
        if m:
            hint = hint[:m.start()]

        idx = self.nextval(hint)
        alias = f'{hint}~{idx}'

        return alias
