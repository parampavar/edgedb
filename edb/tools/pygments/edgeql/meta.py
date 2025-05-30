# AUTOGENERATED BY Gel WITH
#     $ edb gen-meta-grammars edgeql


from __future__ import annotations


class EdgeQL:
    reserved_keywords = (
        "__default__",
        "__edgedbsys__",
        "__edgedbtpl__",
        "__new__",
        "__old__",
        "__source__",
        "__specified__",
        "__std__",
        "__subject__",
        "__type__",
        "administer",
        "alter",
        "analyze",
        "and",
        "anyarray",
        "anyobject",
        "anytuple",
        "anytype",
        "begin",
        "by",
        "case",
        "check",
        "commit",
        "configure",
        "create",
        "deallocate",
        "delete",
        "describe",
        "detached",
        "discard",
        "distinct",
        "do",
        "drop",
        "else",
        "end",
        "except",
        "exists",
        "explain",
        "extending",
        "fetch",
        "filter",
        "for",
        "get",
        "global",
        "grant",
        "group",
        "if",
        "ilike",
        "import",
        "in",
        "insert",
        "intersect",
        "introspect",
        "is",
        "like",
        "limit",
        "listen",
        "load",
        "lock",
        "match",
        "module",
        "move",
        "never",
        "not",
        "notify",
        "offset",
        "on",
        "optional",
        "or",
        "over",
        "partition",
        "prepare",
        "raise",
        "refresh",
        "revoke",
        "rollback",
        "select",
        "set",
        "single",
        "start",
        "typeof",
        "union",
        "update",
        "variadic",
        "when",
        "window",
        "with",
    )
    unreserved_keywords = (
        "abort",
        "abstract",
        "access",
        "after",
        "alias",
        "all",
        "allow",
        "annotation",
        "applied",
        "as",
        "asc",
        "assignment",
        "before",
        "blobal",
        "branch",
        "cardinality",
        "cast",
        "committed",
        "config",
        "conflict",
        "constraint",
        "cube",
        "current",
        "data",
        "database",
        "ddl",
        "declare",
        "default",
        "deferrable",
        "deferred",
        "delegated",
        "deny",
        "desc",
        "each",
        "empty",
        "expression",
        "extension",
        "final",
        "first",
        "force",
        "from",
        "function",
        "future",
        "implicit",
        "index",
        "infix",
        "inheritable",
        "instance",
        "into",
        "isolation",
        "json",
        "last",
        "link",
        "migration",
        "multi",
        "named",
        "object",
        "of",
        "only",
        "onto",
        "operator",
        "optionality",
        "order",
        "orphan",
        "overloaded",
        "owned",
        "package",
        "policy",
        "populate",
        "postfix",
        "prefix",
        "property",
        "proposed",
        "pseudo",
        "read",
        "reject",
        "release",
        "rename",
        "repeatable",
        "required",
        "reset",
        "restrict",
        "rewrite",
        "role",
        "roles",
        "rollup",
        "savepoint",
        "scalar",
        "schema",
        "sdl",
        "serializable",
        "session",
        "source",
        "superuser",
        "system",
        "target",
        "template",
        "ternary",
        "text",
        "then",
        "to",
        "transaction",
        "trigger",
        "type",
        "unless",
        "using",
        "verbose",
        "version",
        "view",
        "write",
    )
    bool_literals = (
        "false",
        "true",
    )
    type_builtins = (
        "Base64Alphabet",
        "BaseObject",
        "ElasticLanguage",
        "Endian",
        "FreeObject",
        "JsonEmpty",
        "Language",
        "LuceneLanguage",
        "Method",
        "Object",
        "PGLanguage",
        "RequestFailureKind",
        "RequestState",
        "Response",
        "ScheduledRequest",
        "Weight",
        "anycontiguous",
        "anydiscrete",
        "anyenum",
        "anyfloat",
        "anyint",
        "anynumeric",
        "anypoint",
        "anyreal",
        "anyscalar",
        "array",
        "bigint",
        "bool",
        "bytes",
        "date",
        "date_duration",
        "datetime",
        "decimal",
        "document",
        "duration",
        "enum",
        "float32",
        "float64",
        "int16",
        "int32",
        "int64",
        "interval",
        "json",
        "local_date",
        "local_datetime",
        "local_time",
        "multirange",
        "range",
        "relative_duration",
        "sequence",
        "str",
        "timestamp",
        "timestamptz",
        "tuple",
        "uuid",
    )
    module_builtins = (
        "cal",
        "cfg",
        "enc",
        "ext",
        "fts",
        "http",
        "math",
        "net",
        "pg",
        "schema",
        "std",
        "sys",
    )
    constraint_builtins = (
        "constraint",
        "exclusive",
        "expression",
        "len_value",
        "max_ex_value",
        "max_len_value",
        "max_value",
        "min_ex_value",
        "min_len_value",
        "min_value",
        "one_of",
        "regexp",
    )
    fn_builtins = (
        "abs",
        "acos",
        "adjacent",
        "all",
        "any",
        "array_agg",
        "array_fill",
        "array_get",
        "array_insert",
        "array_join",
        "array_replace",
        "array_set",
        "array_unpack",
        "asin",
        "assert",
        "assert_distinct",
        "assert_exists",
        "assert_single",
        "atan",
        "atan2",
        "bit_and",
        "bit_count",
        "bit_lshift",
        "bit_not",
        "bit_or",
        "bit_rshift",
        "bit_xor",
        "bounded_above",
        "bounded_below",
        "bytes_get_bit",
        "ceil",
        "contains",
        "cos",
        "cot",
        "count",
        "date_get",
        "datetime_current",
        "datetime_get",
        "datetime_of_statement",
        "datetime_of_transaction",
        "datetime_truncate",
        "duration_get",
        "duration_normalize_days",
        "duration_normalize_hours",
        "duration_to_seconds",
        "duration_truncate",
        "enumerate",
        "find",
        "floor",
        "get_current_branch",
        "get_current_database",
        "get_instance_name",
        "get_transaction_isolation",
        "get_version",
        "get_version_as_str",
        "json_array_unpack",
        "json_get",
        "json_object_pack",
        "json_object_unpack",
        "json_set",
        "json_typeof",
        "len",
        "lg",
        "ln",
        "log",
        "materialized",
        "max",
        "mean",
        "min",
        "multirange",
        "multirange_unpack",
        "overlaps",
        "pi",
        "random",
        "range",
        "range_get_lower",
        "range_get_upper",
        "range_is_empty",
        "range_is_inclusive_lower",
        "range_is_inclusive_upper",
        "range_unpack",
        "re_match",
        "re_match_all",
        "re_replace",
        "re_test",
        "reset_query_stats",
        "round",
        "search",
        "sequence_next",
        "sequence_reset",
        "sin",
        "sqrt",
        "stddev",
        "stddev_pop",
        "str_lower",
        "str_lpad",
        "str_ltrim",
        "str_pad_end",
        "str_pad_start",
        "str_repeat",
        "str_replace",
        "str_reverse",
        "str_rpad",
        "str_rtrim",
        "str_split",
        "str_title",
        "str_trim",
        "str_trim_end",
        "str_trim_start",
        "str_upper",
        "strictly_above",
        "strictly_below",
        "sum",
        "tan",
        "time_get",
        "to_bigint",
        "to_bytes",
        "to_date_duration",
        "to_datetime",
        "to_decimal",
        "to_duration",
        "to_float32",
        "to_float64",
        "to_int16",
        "to_int32",
        "to_int64",
        "to_json",
        "to_local_date",
        "to_local_datetime",
        "to_local_time",
        "to_relative_duration",
        "to_str",
        "to_uuid",
        "uuid_generate_v1mc",
        "uuid_generate_v4",
        "var",
        "var_pop",
        "with_options",
    )
    index_builtins = (
        "brin",
        "btree",
        "gin",
        "gist",
        "hash",
        "index",
        "spgist",
    )
    operators = (
        "!=",
        "%",
        "*",
        "+",
        "++",
        "-",
        "/",
        "//",
        ":=",
        "<",
        "<=",
        "=",
        ">",
        ">=",
        "?!=",
        "?=",
        "??",
        "^",
    )
    navigation = (
        ".<",
        ".>",
        "@",
        ".",
    )
