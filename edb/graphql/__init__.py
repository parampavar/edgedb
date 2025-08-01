#
# This source file is part of the EdgeDB open source project.
#
# Copyright 2016-present MagicStack Inc. and the EdgeDB authors.
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

from .compiler import compile_graphql
from .translator import translate_ast, parse_text, parse_tokens
from .translator import TranspiledOperation
from .tokenizer import Source, NormalizedSource
from .types import GQLCoreSchema

from . import _patch_core
_patch_core.patch_graphql_core()


__all__ = (
    'translate_ast', 'parse_text', 'parse_tokens', 'GQLCoreSchema',
    'compile_graphql', 'TranspiledOperation', 'Source', 'NormalizedSource'
)
