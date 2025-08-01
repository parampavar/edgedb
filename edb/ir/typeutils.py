#
# This source file is part of the EdgeDB open source project.
#
# Copyright 2015-present MagicStack Inc. and the EdgeDB authors.
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

"""Utilities for IR type descriptors."""

from __future__ import annotations
from typing import (
    Any,
    Callable,
    Iterable,
    Optional,
    TYPE_CHECKING,
    overload,
)

import uuid

from edb.edgeql import qltypes

from edb.schema import casts as s_casts
from edb.schema import links as s_links
from edb.schema import name as s_name
from edb.schema import properties as s_props
from edb.schema import pointers as s_pointers
from edb.schema import scalars as s_scalars
from edb.schema import types as s_types
from edb.schema import objtypes as s_objtypes
from edb.schema import objects as s_obj
from edb.schema import utils as s_utils

from . import ast as irast

if TYPE_CHECKING:

    from edb.schema import schema as s_schema


TypeRefCacheKey = tuple[uuid.UUID, bool, bool]
PtrRefCacheKey = s_pointers.PointerLike

PtrRefCache = dict[PtrRefCacheKey, 'irast.BasePointerRef']
TypeRefCache = dict[TypeRefCacheKey, 'irast.TypeRef']


# Modules where all the "types" in them are really just custom views
# provided by metaschema.
VIEW_MODULES = ('sys', 'cfg')


def is_cfg_view(
    obj: s_obj.Object,
    schema: s_schema.Schema,
) -> bool:
    return (
        isinstance(obj, (s_objtypes.ObjectType, s_pointers.Pointer))
        and (
            obj.get_name(schema).module in VIEW_MODULES
            or bool(
                (cfg_object := schema.get(
                    'cfg::ConfigObject',
                    type=s_objtypes.ObjectType, default=None
                ))
                and (
                    nobj := (
                        obj if isinstance(obj, s_objtypes.ObjectType)
                        else obj.get_source(schema)
                    )
                )
                and nobj.issubclass(schema, cfg_object)
            )
        )
    )


def is_excluded_cfg_view(
    child: s_obj.Object,
    *,
    ancestor: s_obj.Object,
    schema: s_schema.Schema,
) -> bool:
    """Used to exclude sys/cfg tables from non sys/cfg views for performance.

    Also used by access policies to prevent including cfg views in
    when expanding a non-cfg type's descendants (#8865).
    """
    return is_cfg_view(child, schema) and not is_cfg_view(ancestor, schema)


def is_scalar(typeref: irast.TypeRef) -> bool:
    """Return True if *typeref* describes a scalar type."""
    return typeref.is_scalar


def is_object(typeref: irast.TypeRef) -> bool:
    """Return True if *typeref* describes an object type."""
    return (
        not is_scalar(typeref)
        and not is_collection(typeref)
        and not is_generic(typeref)
    )


def is_view(typeref: irast.TypeRef) -> bool:
    """Return True if *typeref* describes a view."""
    return typeref.is_view


def is_collection(typeref: irast.TypeRef) -> bool:
    """Return True if *typeref* describes an collection type."""
    return bool(typeref.collection)


def is_array(typeref: irast.TypeRef) -> bool:
    """Return True if *typeref* describes an array type."""
    return typeref.collection == s_types.Array.get_schema_name()


def is_tuple(typeref: irast.TypeRef) -> bool:
    """Return True if *typeref* describes a tuple type."""
    return typeref.collection == s_types.Tuple.get_schema_name()


def is_range(typeref: irast.TypeRef) -> bool:
    """Return True if *typeref* describes a range type."""
    return typeref.collection == s_types.Range.get_schema_name()


def is_multirange(typeref: irast.TypeRef) -> bool:
    """Return True if *typeref* describes a multirange type."""
    return typeref.collection == s_types.MultiRange.get_schema_name()


def is_any(typeref: irast.TypeRef) -> bool:
    """Return True if *typeref* describes the ``anytype`` generic type."""
    return isinstance(typeref, irast.AnyTypeRef)


def is_anytuple(typeref: irast.TypeRef) -> bool:
    """Return True if *typeref* describes the ``anytuple`` generic type."""
    return isinstance(typeref, irast.AnyTupleRef)


def is_anyobject(typeref: irast.TypeRef) -> bool:
    """Return True if *typeref* describes the ``anyobject`` generic type."""
    return isinstance(typeref, irast.AnyObjectRef)


def is_generic(typeref: irast.TypeRef) -> bool:
    """Return True if *typeref* describes a generic type."""
    if is_collection(typeref):
        return any(is_generic(st) for st in typeref.subtypes)
    else:
        return is_any(typeref) or is_anytuple(typeref) or is_anyobject(typeref)


def is_abstract(typeref: irast.TypeRef) -> bool:
    """Return True if *typeref* describes an abstract type."""
    return typeref.is_abstract


def is_json(typeref: irast.TypeRef) -> bool:
    """Return True if *typeref* describes the json type."""
    return typeref.real_base_type.id == s_obj.get_known_type_id('std::json')


def is_bytes(typeref: irast.TypeRef) -> bool:
    """Return True if *typeref* describes the bytes type."""
    return typeref.real_base_type.id == s_obj.get_known_type_id('std::bytes')


def is_exactly_free_object(typeref: irast.TypeRef) -> bool:
    return typeref.name_hint == s_name.QualName('std', 'FreeObject')


def is_free_object(typeref: irast.TypeRef) -> bool:
    if typeref.material_type:
        typeref = typeref.material_type
    return is_exactly_free_object(typeref)


def is_persistent_tuple(typeref: irast.TypeRef) -> bool:
    if is_tuple(typeref):
        if typeref.material_type is not None:
            material = typeref.material_type
        else:
            material = typeref

        return material.in_schema
    else:
        return False


def is_empty_typeref(typeref: irast.TypeRef) -> bool:
    return typeref.union is not None and len(typeref.union) == 0


def needs_custom_serialization(typeref: irast.TypeRef) -> bool:
    # True if any component needs custom serialization
    return contains_predicate(
        typeref,
        lambda typeref:
            typeref.real_base_type.custom_sql_serialization is not None
    )


def contains_predicate(
    typeref: irast.TypeRef,
    pred: Callable[[irast.TypeRef], bool],
) -> bool:
    if pred(typeref):
        return True

    elif typeref.union:
        return any(
            contains_predicate(sub, pred) for sub in typeref.union
        )
    return any(
        contains_predicate(sub, pred) for sub in typeref.subtypes
    )


def contains_object(typeref: irast.TypeRef) -> bool:
    return contains_predicate(typeref, is_object)


def type_to_typeref(
    schema: s_schema.Schema,
    t: s_types.Type,
    *,
    cache: Optional[dict[TypeRefCacheKey, irast.TypeRef]],
    typename: Optional[s_name.QualName] = None,
    include_children: bool = False,
    include_ancestors: bool = False,
    _name: Optional[str] = None,
) -> irast.TypeRef:
    """Return an instance of :class:`ir.ast.TypeRef` for a given type.

    An IR TypeRef is an object that fully describes a schema type for
    the purposes of query compilation.

    Args:
        schema:
            A schema instance, in which the type *t* is defined.
        t:
            A schema type instance.
        cache:
            Optional mapping from (type UUID, typename) to cached IR TypeRefs.
        typename:
            Optional name hint to use for the type in the returned
            TypeRef.  If ``None``, the type name is used.
        include_children:
            Whether to include the description of all material type children
            of *t*.
        include_ancestors:
            Whether to include the description of all material type ancestors
            of *t*.
        _name:
            Optional subtype element name if this type is a collection within
            a Tuple,

    Returns:
        A ``TypeRef`` instance corresponding to the given schema type.
    """

    if cache is not None and typename is None:
        key = (t.id, include_children, include_ancestors)

        cached_result = cache.get(key)
        if cached_result is not None:
            # If the schema changed due to an ongoing compilation, the name
            # hint might be outdated.
            if cached_result.name_hint == t.get_name(schema):
                return cached_result

    # We separate the uncached version into another function because
    # it makes it easy to tell in a profiler when the cache isn't
    # operating, and because if the cache *is* operating it is no
    # great loss.
    return _type_to_typeref(
        schema,
        t,
        cache=cache,
        typename=typename,
        include_children=include_children,
        include_ancestors=include_ancestors,
        _name=_name,
    )


def _type_to_typeref(
    schema: s_schema.Schema,
    t: s_types.Type,
    *,
    cache: Optional[dict[TypeRefCacheKey, irast.TypeRef]] = None,
    typename: Optional[s_name.QualName] = None,
    include_children: bool = False,
    include_ancestors: bool = False,
    _name: Optional[str] = None,
) -> irast.TypeRef:

    def _typeref(
        t: s_types.Type,
        *,
        include_children: bool = include_children,
        include_ancestors: bool = include_ancestors,
    ) -> irast.TypeRef:
        return type_to_typeref(
            schema,
            t,
            include_children=include_children,
            include_ancestors=include_ancestors,
            cache=cache,
        )

    result: irast.TypeRef
    material_type: s_types.Type

    name_hint = typename or t.get_name(schema)
    orig_name_hint = None if not typename else t.get_name(schema)

    if t.is_anytuple(schema):
        result = irast.AnyTupleRef(
            id=t.id,
            name_hint=name_hint,
            orig_name_hint=orig_name_hint,
        )
    elif t.is_anyobject(schema):
        result = irast.AnyObjectRef(
            id=t.id,
            name_hint=name_hint,
            orig_name_hint=orig_name_hint,
        )
    elif t.is_any(schema):
        result = irast.AnyTypeRef(
            id=t.id,
            name_hint=name_hint,
            orig_name_hint=orig_name_hint,
        )
    elif not isinstance(t, s_types.Collection):
        assert isinstance(t, s_types.InheritingType)

        union: Optional[frozenset[irast.TypeRef]] = None
        union_is_exhaustive: bool = False
        expr_intersection: Optional[frozenset[irast.TypeRef]] = None
        expr_union: Optional[frozenset[irast.TypeRef]] = None
        if t.is_union_type(schema) or t.is_intersection_type(schema):
            union_types, union_is_exhaustive = (
                s_utils.get_type_expr_non_overlapping_union(t, schema)
            )

            union = frozenset(
                _typeref(c) for c in union_types
            )

            # Keep track of type expression structure.
            # This is necessary to determine the correct rvar when doing
            # type intersections or polymorphic queries.
            if expr_intersection_types := t.get_intersection_of(schema):
                expr_intersection = frozenset(
                    _typeref(c)
                    for c in expr_intersection_types.objects(schema)
                )

            if expr_union_types := t.get_union_of(schema):
                expr_union = frozenset(
                    _typeref(c)
                    for c in expr_union_types.objects(schema)
                )

        schema, material_type = t.material_type(schema)

        material_typeref: Optional[irast.TypeRef]
        if material_type != t:
            material_typeref = _typeref(material_type)
        else:
            material_typeref = None

        if (isinstance(material_type, s_scalars.ScalarType)
                and not material_type.get_abstract(schema)):
            base_type = material_type.get_topmost_concrete_base(schema)
            if base_type == material_type:
                base_typeref = None
            else:
                assert isinstance(base_type, s_types.Type)
                base_typeref = _typeref(base_type, include_children=False)
        else:
            base_typeref = None

        children: Optional[frozenset[irast.TypeRef]] = None
        if (
            material_typeref is None
            and include_children
            and children is None
        ):
            children = frozenset(
                _typeref(child, include_children=True)
                for child in t.children(schema)
                if not child.get_is_derived(schema)
                and not child.is_compound_type(schema)
            )

        ancestors: Optional[frozenset[irast.TypeRef]] = None
        if (
            material_typeref is None
            and include_ancestors
            and ancestors is None
        ):
            ancestors = frozenset(
                _typeref(ancestor, include_ancestors=False)
                for ancestor in t.get_ancestors(schema).objects(schema)
            )

        sql_type = None
        needs_custom_json_cast = False
        custom_sql_serialization = None
        if isinstance(t, s_scalars.ScalarType):
            sql_type = t.resolve_sql_type(schema)
            if material_typeref is None:
                cast_name = s_casts.get_cast_fullname_from_names(
                    orig_name_hint or name_hint,
                    s_name.QualName('std', 'json'))
                jcast = schema.get(cast_name, type=s_casts.Cast, default=None)
                if jcast:
                    needs_custom_json_cast = bool(jcast.get_code(schema))

            custom_sql_serialization = t.get_custom_sql_serialization(schema)

        result = irast.TypeRef(
            id=t.id,
            name_hint=name_hint,
            orig_name_hint=orig_name_hint,
            material_type=material_typeref,
            base_type=base_typeref,
            children=children,
            ancestors=ancestors,
            union=union,
            union_is_exhaustive=union_is_exhaustive,
            expr_intersection=expr_intersection,
            expr_union=expr_union,
            element_name=_name,
            is_scalar=t.is_scalar(),
            is_abstract=t.get_abstract(schema),
            is_view=t.is_view(schema),
            is_cfg_view=is_cfg_view(t, schema),
            is_opaque_union=t.get_is_opaque_union(schema),
            needs_custom_json_cast=needs_custom_json_cast,
            sql_type=sql_type,
            custom_sql_serialization=custom_sql_serialization,
        )
    elif isinstance(t, s_types.Tuple) and t.is_named(schema):
        schema, material_type = t.material_type(schema)

        if material_type != t:
            material_typeref = _typeref(material_type)
        else:
            material_typeref = None

        result = irast.TypeRef(
            id=t.id,
            name_hint=name_hint,
            orig_name_hint=orig_name_hint,
            material_type=material_typeref,
            element_name=_name,
            collection=t.get_schema_name(),
            in_schema=t.get_is_persistent(schema),
            subtypes=tuple(
                # ??? no cache
                type_to_typeref(schema, st, _name=sn, cache=None)
                for sn, st in t.iter_subtypes(schema)
            )
        )
    else:
        schema, material_type = t.material_type(schema)

        if material_type != t:
            material_typeref = type_to_typeref(
                schema, material_type, cache=cache
            )
        else:
            material_typeref = None

        result = irast.TypeRef(
            id=t.id,
            name_hint=name_hint,
            orig_name_hint=orig_name_hint,
            material_type=material_typeref,
            element_name=_name,
            collection=t.get_schema_name(),
            in_schema=t.get_is_persistent(schema),
            subtypes=tuple(
                _typeref(st) for st in t.get_subtypes(schema)
            )
        )

    if cache is not None and typename is None and _name is None:
        key = (t.id, include_children, include_ancestors)

        # Note: there is no cache for `_name` variants since they are only used
        # for Tuple subtypes and thus they will be cached on the outer level
        # anyway.
        # There's also no variant for types with custom typenames since they
        # proved to have a very low hit rate.
        # This way we save on the size of the key tuple.
        cache[key] = result
    return result


def ir_typeref_to_type(
    schema: s_schema.Schema,
    typeref: irast.TypeRef,
) -> tuple[s_schema.Schema, s_types.Type]:
    """Return a schema type for a given IR TypeRef.

    This is the reverse of :func:`~type_to_typeref`.

    Args:
        schema:
            A schema instance. The result type must exist in it.
        typeref:
            A :class:`ir.ast.TypeRef` instance for which to return
            the corresponding schema type.

    Returns:
        A tuple containing the possibly modified schema and
        a :class:`schema.types.Type` instance corresponding to the
        given *typeref*.
    """
    # Optimistically try to lookup the type by id. Sometimes for
    # arrays and tuples this will fail, and we'll need to create it.
    t = schema.get_by_id(typeref.id, default=None, type=s_types.Type)
    if t:
        return schema, t

    elif is_tuple(typeref):
        named = False
        tuple_subtypes = {}
        for si, st in enumerate(typeref.subtypes):
            if st.element_name:
                named = True
                type_name = st.element_name
            else:
                type_name = str(si)

            schema, st_t = ir_typeref_to_type(schema, st)
            tuple_subtypes[type_name] = st_t

        return s_types.Tuple.from_subtypes(
            schema, tuple_subtypes, {'named': named})

    elif is_array(typeref):
        array_subtypes = []
        for st in typeref.subtypes:
            schema, st_t = ir_typeref_to_type(schema, st)
            array_subtypes.append(st_t)

        return s_types.Array.from_subtypes(schema, array_subtypes)

    else:
        raise AssertionError("couldn't find type from typeref")


@overload
def ptrref_from_ptrcls(
    *,
    schema: s_schema.Schema,
    ptrcls: s_pointers.Pointer,
    cache: Optional[PtrRefCache],
    typeref_cache: Optional[TypeRefCache],
) -> irast.PointerRef:
    ...


@overload
def ptrref_from_ptrcls(
    *,
    schema: s_schema.Schema,
    ptrcls: s_pointers.PointerLike,
    cache: Optional[PtrRefCache],
    typeref_cache: Optional[TypeRefCache],
) -> irast.BasePointerRef:
    ...


def ptrref_from_ptrcls(
    *,
    schema: s_schema.Schema,
    ptrcls: s_pointers.PointerLike,
    cache: Optional[PtrRefCache],
    typeref_cache: Optional[TypeRefCache],
) -> irast.BasePointerRef:
    """Return an IR pointer descriptor for a given schema pointer.

    An IR PointerRef is an object that fully describes a schema pointer for
    the purposes of query compilation.

    Args:
        schema:
            A schema instance, in which the type *t* is defined.
        ptrcls:
            A :class:`schema.pointers.Pointer` instance for which to
            return the PointerRef.
        direction:
            The direction of the pointer in the path expression.

    Returns:
        An instance of a subclass of :class:`ir.ast.BasePointerRef`
        corresponding to the given schema pointer.
    """

    if cache is not None:
        cached = cache.get(ptrcls)
        if cached is not None:
            return cached

    kwargs: dict[str, Any] = {}

    ircls: type[irast.BasePointerRef]

    source_ref: Optional[irast.TypeRef]
    target_ref: Optional[irast.TypeRef]
    out_source: Optional[irast.TypeRef]

    if isinstance(ptrcls, irast.TupleIndirectionLink):
        ircls = irast.TupleIndirectionPointerRef
    elif isinstance(ptrcls, irast.TypeIntersectionLink):
        ircls = irast.TypeIntersectionPointerRef
        kwargs['optional'] = ptrcls.is_optional()
        kwargs['is_empty'] = ptrcls.is_empty()
        kwargs['is_subtype'] = ptrcls.is_subtype()
        kwargs['rptr_specialization'] = ptrcls.get_rptr_specialization()
    elif isinstance(ptrcls, s_pointers.Pointer):
        ircls = irast.PointerRef
        kwargs['id'] = ptrcls.id
        kwargs['defined_here'] = ptrcls.get_defined_here(schema)
        if backlink := ptrcls.get_computed_link_alias(schema):
            assert isinstance(backlink, s_pointers.Pointer)
            kwargs['computed_link_alias'] = ptrref_from_ptrcls(
                ptrcls=backlink, schema=schema,
                cache=cache, typeref_cache=typeref_cache,
            )
            kwargs['computed_link_alias_is_backward'] = (
                ptrcls.get_computed_link_alias_is_backward(schema))

    else:
        raise AssertionError(f'unexpected pointer class: {ptrcls}')

    target = ptrcls.get_target(schema)
    if target is not None and not isinstance(target, irast.TypeRef):
        assert isinstance(target, s_types.Type)
        target_ref = type_to_typeref(
            schema, target, include_children=True, cache=typeref_cache)
    else:
        target_ref = target

    source = ptrcls.get_source(schema)

    source_ptr: Optional[irast.BasePointerRef]
    if (isinstance(ptrcls, s_props.Property)
            and isinstance(source, s_links.Link)):
        source_ptr = ptrref_from_ptrcls(
            ptrcls=source,
            schema=schema,
            cache=cache,
            typeref_cache=typeref_cache,
        )
        source_ref = None
    else:
        if source is not None and not isinstance(source, irast.TypeRef):
            assert isinstance(source, s_types.Type)
            source_ref = type_to_typeref(schema,
                                         source,
                                         include_ancestors=True,
                                         cache=typeref_cache)
        else:
            source_ref = source
        source_ptr = None

    out_source = source_ref
    out_target = target_ref

    out_cardinality, in_cardinality = cardinality_from_ptrcls(
        schema, ptrcls)

    schema, material_ptrcls = ptrcls.material_type(schema)
    material_ptr: Optional[irast.BasePointerRef]
    if material_ptrcls is not None and material_ptrcls != ptrcls:
        material_ptr = ptrref_from_ptrcls(
            ptrcls=material_ptrcls,
            schema=schema,
            cache=cache,
            typeref_cache=typeref_cache,
        )
    else:
        material_ptr = None

    union_components: Optional[set[irast.BasePointerRef]] = None
    union_of = ptrcls.get_union_of(schema)
    union_is_exhaustive = False
    if union_of:
        union_ptrs = set()

        for component in union_of.objects(schema):
            assert isinstance(component, s_pointers.Pointer)
            schema, material_comp = component.material_type(schema)
            union_ptrs.add(material_comp)

        non_overlapping, union_is_exhaustive = (
            s_utils.get_non_overlapping_union(
                schema,
                union_ptrs,
            )
        )

        union_components = {
            ptrref_from_ptrcls(
                ptrcls=p,
                schema=schema,
                cache=cache,
                typeref_cache=typeref_cache,
            ) for p in non_overlapping
        }

    intersection_components: Optional[set[irast.BasePointerRef]] = None
    intersection_of = ptrcls.get_intersection_of(schema)
    if intersection_of:
        intersection_ptrs = set()

        for component in intersection_of.objects(schema):
            assert isinstance(component, s_pointers.Pointer)
            schema, material_comp = component.material_type(schema)
            intersection_ptrs.add(material_comp)

        intersection_components = {
            ptrref_from_ptrcls(
                ptrcls=p,
                schema=schema,
                cache=cache,
                typeref_cache=typeref_cache,
            ) for p in intersection_ptrs
        }

    std_parent_name = None
    for ancestor in ptrcls.get_ancestors(schema).objects(schema):
        ancestor_name = ancestor.get_name(schema)
        if ancestor_name.module == 'std' and ancestor.is_non_concrete(schema):
            std_parent_name = ancestor_name
            break

    is_derived = ptrcls.get_is_derived(schema)
    base_ptr: Optional[irast.BasePointerRef]
    if is_derived:
        base_ptrcls = ptrcls.get_bases(schema).first(schema)
        top_ptr_name = type(base_ptrcls).get_default_base_name()
        if base_ptrcls.get_name(schema) != top_ptr_name:
            base_ptr = ptrref_from_ptrcls(
                ptrcls=base_ptrcls,
                schema=schema,
                cache=cache,
                typeref_cache=typeref_cache,
            )
        else:
            base_ptr = None
    else:
        base_ptr = None

    if (
        material_ptr is None
        and isinstance(ptrcls, s_pointers.Pointer)
    ):
        children = frozenset(
            ptrref_from_ptrcls(
                ptrcls=child,
                schema=schema,
                cache=cache,
                typeref_cache=typeref_cache,
            )
            for child in ptrcls.children(schema)
            if not child.get_is_derived(schema)
        )
    else:
        children = frozenset()

    kwargs.update(
        dict(
            out_source=out_source,
            out_target=out_target,
            name=ptrcls.get_name(schema),
            shortname=ptrcls.get_shortname(schema),
            std_parent_name=std_parent_name,
            source_ptr=source_ptr,
            base_ptr=base_ptr,
            material_ptr=material_ptr,
            children=children,
            is_derived=ptrcls.get_is_derived(schema),
            is_computable=ptrcls.get_computable(schema),
            union_components=union_components,
            intersection_components=intersection_components,
            union_is_exhaustive=union_is_exhaustive,
            has_properties=ptrcls.has_user_defined_properties(schema),
            in_cardinality=in_cardinality,
            out_cardinality=out_cardinality,
        )
    )

    ptrref = ircls(**kwargs)

    if cache is not None:
        cache[ptrcls] = ptrref

        # This is kind of unfortunate, but if we are caching, update the
        # base_ptr with this child
        if base_ptr and not material_ptr and ptrref not in base_ptr.children:
            base_ptr.children = base_ptr.children | frozenset([ptrref])

    return ptrref


@overload
def ptrcls_from_ptrref(
    ptrref: irast.PointerRef,
    *,
    schema: s_schema.Schema,
) -> tuple[s_schema.Schema, s_pointers.Pointer]:
    ...


@overload
def ptrcls_from_ptrref(
    ptrref: irast.BasePointerRef,
    *,
    schema: s_schema.Schema,
) -> tuple[s_schema.Schema, s_pointers.PointerLike]:
    ...


def ptrcls_from_ptrref(
    ptrref: irast.BasePointerRef,
    *,
    schema: s_schema.Schema,
) -> tuple[s_schema.Schema, s_pointers.PointerLike]:
    """Return a schema pointer for a given IR PointerRef.

    This is the reverse of :func:`~type_to_typeref`.

    Args:
        schema:
            A schema instance. The result type must exist in it.
        ptrref:
            A :class:`ir.ast.BasePointerRef` instance for which to return
            the corresponding schema pointer.

    Returns:
        A tuple containing the possibly modifed schema and
        a :class:`schema.pointers.PointerLike` instance corresponding to the
        given *ptrref*.
    """

    ptrcls: s_pointers.PointerLike

    if isinstance(ptrref, irast.TupleIndirectionPointerRef):
        schema, src_t = ir_typeref_to_type(schema, ptrref.out_source)
        schema, tgt_t = ir_typeref_to_type(schema, ptrref.out_target)
        ptrcls = irast.TupleIndirectionLink(
            source=src_t,
            target=tgt_t,
            element_name=ptrref.name.name,
        )
    elif isinstance(ptrref, irast.TypeIntersectionPointerRef):
        target = schema.get_by_id(ptrref.out_target.id)
        assert isinstance(target, s_types.Type)
        ptrcls = irast.TypeIntersectionLink(
            source=schema.get_by_id(ptrref.out_source.id),
            target=target,
            optional=ptrref.optional,
            is_empty=ptrref.is_empty,
            is_subtype=ptrref.is_subtype,
            cardinality=ptrref.out_cardinality.to_schema_value()[1],
        )
    elif isinstance(ptrref, irast.PointerRef):
        ptr = schema.get_by_id(ptrref.id)
        assert isinstance(ptr, s_pointers.Pointer)
        ptrcls = ptr
    else:
        raise TypeError(f'unexpected pointer ref type: {ptrref!r}')

    return schema, ptrcls


def cardinality_from_ptrcls(
    schema: s_schema.Schema,
    ptrcls: s_pointers.PointerLike,
) -> tuple[Optional[qltypes.Cardinality], Optional[qltypes.Cardinality]]:

    out_card = ptrcls.get_cardinality(schema)
    required = ptrcls.get_required(schema)
    if out_card is None or not out_card.is_known():
        # The cardinality is not yet known.
        out_cardinality = None
        in_cardinality = None
    else:
        assert isinstance(out_card, qltypes.SchemaCardinality)
        out_cardinality = qltypes.Cardinality.from_schema_value(
            required, out_card)
        # Backward link cannot be required, but exclusivity
        # controls upper bound on cardinality.
        if not ptrcls.is_non_concrete(schema) and ptrcls.is_exclusive(schema):
            in_cardinality = qltypes.Cardinality.AT_MOST_ONE
        else:
            in_cardinality = qltypes.Cardinality.MANY

    return out_cardinality, in_cardinality


def is_id_ptrref(ptrref: irast.BasePointerRef) -> bool:
    """Return True if *ptrref* describes the id property."""
    return (
        str(ptrref.std_parent_name) == 'std::id'
    ) and not ptrref.source_ptr


def is_computable_ptrref(ptrref: irast.BasePointerRef) -> bool:
    """Return True if pointer described by *ptrref* is computed."""
    return ptrref.is_computable


def get_tuple_element_index(ptrref: irast.TupleIndirectionPointerRef) -> int:
    name = ptrref.name.name
    if name.isdecimal() and name.isascii():
        return int(name)
    else:
        for i, st in enumerate(ptrref.out_source.subtypes):
            if st.element_name == name:
                return i

        raise AssertionError(f"element {name} is not found in tuple type")


def type_contains(
    parent: irast.TypeRef,
    child: irast.TypeRef,
) -> bool:
    """Check if *parent* typeref contains the given *child* typeref.

    Both *parent* and *child* can be type expressions.
    """
    if parent == child:
        return True

    # Calculate the minterms of both *parent* and *child*.
    parent_minterms = _disjunctive_normal_form(parent)
    child_minterms = _disjunctive_normal_form(child)

    # The *parent* contains *child* if each child minterm is contained
    # by a parent minterm.
    #
    # Examples
    # - [A] contains [AB]
    # - [A,B] contains [A]
    # - [AB] does not contain [A]
    # - [A] does not contain [A,B]
    # - [AB,CD] does not contain [BD]
    return all(
        any(
            c.issuperset(p)
            for p in parent_minterms
        )
        for c in child_minterms
    )


def _disjunctive_normal_form(
    typeref: irast.TypeRef
) -> list[set[uuid.UUID]]:
    """Convert any typeref into a minimal disjunctive normal form.

    In the result:
    - The outer list represents unions.
    - The inner sets represent intersections of simple types (ie. minterms).

    Duplicate and superset minterms are removed as redundant.
    """

    def simplify(
        expr: Iterable[set[uuid.UUID]]
    ) -> list[set[uuid.UUID]]:
        # Remove any minterms which imply others
        # eg. [A, AB, BC] -> [A, BC]
        minterms_by_length = sorted(
            expr,
            key=lambda i: len(i)
        )

        result: list[set[uuid.UUID]] = []
        for minterm in minterms_by_length:
            if not any(
                minterm.issuperset(r)
                for r in result
            ):
                result.append(minterm)

        return result

    if typeref.expr_union:
        return simplify(
            minterm
            for t in typeref.expr_union
            for minterm in _disjunctive_normal_form(t)
        )

    elif typeref.expr_intersection:
        components = [
            _disjunctive_normal_form(t)
            for t in typeref.expr_intersection
        ]

        result = components[0]
        for other in components[1:]:
            result = [
                set.union(r, o)
                for r in result
                for o in other
            ]

        return simplify(result)

    else:
        return [{typeref.id}]


def find_actual_ptrref(
    source_typeref: irast.TypeRef,
    parent_ptrref: irast.BasePointerRef,
    *,
    dir: s_pointers.PointerDirection = s_pointers.PointerDirection.Outbound,
    material: bool=True,
) -> irast.BasePointerRef:
    if material and source_typeref.material_type:
        source_typeref = source_typeref.material_type

    if material and parent_ptrref.material_ptr:
        parent_ptrref = parent_ptrref.material_ptr

    ptrref = parent_ptrref

    if ptrref.source_ptr is not None:
        # Link property ref
        link_ptr: irast.BasePointerRef = ptrref.source_ptr
        if link_ptr.material_ptr:
            link_ptr = link_ptr.material_ptr
        if link_ptr.dir_source(dir).id == source_typeref.id:
            return ptrref
    elif ptrref.dir_source(dir).id == source_typeref.id:
        return ptrref

    # We are updating a subtype, find the
    # correct descendant ptrref.
    for dp in (
        (ptrref.union_components or set())
        | (ptrref.intersection_components or set())
    ):
        candidate = maybe_find_actual_ptrref(
            source_typeref, dp, material=material, dir=dir)
        if candidate is not None:
            return candidate

    for dp in ptrref.children:
        if dp.dir_source(dir) and dp.dir_source(dir).id == source_typeref.id:
            return dp
        else:
            candidate = maybe_find_actual_ptrref(
                source_typeref, dp, material=material, dir=dir)
            if candidate is not None:
                return candidate

    raise LookupError(
        f'cannot find ptrref matching typeref {source_typeref.id}')


def maybe_find_actual_ptrref(
    source_typeref: irast.TypeRef,
    parent_ptrref: irast.BasePointerRef,
    *,
    material: bool=True,
    dir: s_pointers.PointerDirection = s_pointers.PointerDirection.Outbound,
) -> Optional[irast.BasePointerRef]:
    try:
        return find_actual_ptrref(
            source_typeref, parent_ptrref, material=material, dir=dir)
    except LookupError:
        return None


def get_typeref_descendants(typeref: irast.TypeRef) -> set[irast.TypeRef]:
    result = set()
    if typeref.children:
        for child in typeref.children:
            result.add(child)
            result.update(get_typeref_descendants(child))

    return result


def maybe_lookup_obj_pointer(
    schema: s_schema.Schema,
    name: s_name.QualName,
    ptr_name: s_name.UnqualName,
) -> Optional[s_pointers.Pointer]:
    base_object = schema.get(name, type=s_objtypes.ObjectType, default=None)
    if not base_object:
        return None
    ptr = base_object.maybe_get_ptr(schema, ptr_name)
    return ptr


def lookup_obj_ptrref(
    schema: s_schema.Schema,
    name: s_name.QualName,
    ptr_name: s_name.UnqualName,
    cache: Optional[dict[PtrRefCacheKey, irast.BasePointerRef]] = None,
    typeref_cache: Optional[dict[TypeRefCacheKey, irast.TypeRef]] = None,
) -> irast.PointerRef:
    ptr = maybe_lookup_obj_pointer(schema, name, ptr_name)
    assert ptr
    return ptrref_from_ptrcls(
        ptrcls=ptr, schema=schema, cache=cache, typeref_cache=typeref_cache,
    )


def replace_pathid_prefix(
    path_id: irast.PathId,
    prefix: irast.PathId,
    replacement: irast.PathId,
    permissive_ptr_path: bool=False,
) -> irast.PathId:
    """Return a copy of *path_id* with *prefix* replaced by
       *replacement*.

       Example:

           replace_pathid_prefix(A.b.c, A.b, X.y) == PathId(X.y.c)
    """
    if not path_id.startswith(prefix, permissive_ptr_path=permissive_ptr_path):
        return path_id

    # TODO: iter_prefixes is kind of expensive; can we do this in a
    # way that peeks into the internals more?

    result = replacement
    prefixes = list(path_id.iter_prefixes(include_ptr=prefix.is_ptr_path()))
    lastns = prefix.namespace

    try:
        start = prefixes.index(prefix)
    except ValueError:
        if permissive_ptr_path:
            start = prefixes.index(prefix.ptr_path())
        else:
            raise

    for part in prefixes[start + 1:]:
        if part.is_ptr_path():
            continue

        ptrref = part.rptr()
        if not ptrref:
            continue
        dir = part.rptr_dir()
        assert dir

        if (
            isinstance(ptrref, irast.TupleIndirectionPointerRef)
            and result.target.collection == 'tuple'
        ):
            # For tuple indirections, we want to update the target
            # type when we get mapped to a subtype.
            idx = get_tuple_element_index(ptrref)
            target = result.target
            if target.id != target.subtypes[idx].id:
                ptrref = ptrref.replace(
                    out_source=target,
                    out_target=target.subtypes[idx],
                )

        if ptrref.source_ptr:
            result = result.ptr_path()
        result = result.extend(
            ptrref=ptrref, direction=dir, ns=part.namespace - lastns)
        lastns = part.namespace

    if path_id.is_ptr_path():
        result = result.ptr_path()

    return result
