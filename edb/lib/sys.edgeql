#
# This source file is part of the EdgeDB open source project.
#
# Copyright 2018-present MagicStack Inc. and the EdgeDB authors.
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


CREATE MODULE sys;


CREATE MODULE sys::perm;
CREATE PERMISSION sys::perm::superuser;
CREATE PERMISSION sys::perm::data_modification;
CREATE PERMISSION sys::perm::ddl;
CREATE PERMISSION sys::perm::branch_config;
CREATE PERMISSION sys::perm::sql_session_config;


CREATE SCALAR TYPE sys::TransactionIsolation
    EXTENDING enum<RepeatableRead, Serializable>;


CREATE SCALAR TYPE sys::TransactionAccessMode
    EXTENDING enum<ReadOnly, ReadWrite>;


CREATE SCALAR TYPE sys::TransactionDeferrability
    EXTENDING enum<Deferrable, NotDeferrable>;


CREATE SCALAR TYPE sys::VersionStage
    EXTENDING enum<dev, alpha, beta, rc, final>;


CREATE SCALAR TYPE sys::QueryType
    EXTENDING enum<EdgeQL, SQL>;


CREATE SCALAR TYPE sys::OutputFormat
    EXTENDING enum<BINARY, JSON, JSON_ELEMENTS, NONE>;


CREATE ABSTRACT TYPE sys::SystemObject EXTENDING schema::Object;

CREATE ABSTRACT TYPE sys::ExternalObject EXTENDING sys::SystemObject;


CREATE TYPE sys::Branch EXTENDING
        sys::ExternalObject,
        schema::AnnotationSubject {
    ALTER PROPERTY name {
        CREATE CONSTRAINT std::exclusive;
    };
    CREATE PROPERTY last_migration-> std::str;
};

CREATE ALIAS sys::Database := sys::Branch;


CREATE TYPE sys::ExtensionPackage EXTENDING
        sys::SystemObject,
        schema::AnnotationSubject {
    CREATE REQUIRED PROPERTY script -> str;
    CREATE REQUIRED PROPERTY version ->
        tuple<
             major: std::int64,
             minor: std::int64,
             stage: sys::VersionStage,
             stage_no: std::int64,
             local: array<std::str>,
         >;
};

CREATE TYPE sys::ExtensionPackageMigration EXTENDING
        sys::SystemObject,
        schema::AnnotationSubject {
    CREATE REQUIRED PROPERTY script -> str;
    CREATE REQUIRED PROPERTY from_version ->
        tuple<
             major: std::int64,
             minor: std::int64,
             stage: sys::VersionStage,
             stage_no: std::int64,
             local: array<std::str>,
         >;
    CREATE REQUIRED PROPERTY to_version ->
        tuple<
             major: std::int64,
             minor: std::int64,
             stage: sys::VersionStage,
             stage_no: std::int64,
             local: array<std::str>,
         >;
};


ALTER TYPE schema::Extension {
    CREATE REQUIRED LINK package -> sys::ExtensionPackage {
        CREATE CONSTRAINT std::exclusive;
    }
};


CREATE TYPE sys::Role EXTENDING
        sys::SystemObject,
        schema::InheritingObject,
        schema::AnnotationSubject {
    ALTER PROPERTY name {
        CREATE CONSTRAINT std::exclusive;
    };

    CREATE REQUIRED PROPERTY superuser -> std::bool;
    # Backwards compatibility.
    CREATE PROPERTY is_superuser := .superuser;
    CREATE PROPERTY password -> std::str;
    CREATE MULTI PROPERTY permissions -> std::str;
    CREATE MULTI PROPERTY branches -> std::str;

    CREATE ACCESS POLICY ap_read allow select using (
        global sys::perm::superuser
    );
};


ALTER TYPE sys::Role {
    CREATE MULTI LINK member_of -> sys::Role;
};


CREATE TYPE sys::QueryStats EXTENDING sys::ExternalObject {
    CREATE LINK branch -> sys::Branch {
        CREATE ANNOTATION std::description :=
            "The branch this statistics entry was collected in.";
    };
    CREATE PROPERTY query -> std::str {
        CREATE ANNOTATION std::description :=
            "Text string of a representative query.";
    };
    CREATE PROPERTY query_type -> sys::QueryType {
        CREATE ANNOTATION std::description :=
            "Type of the query.";
    };
    CREATE PROPERTY tag -> std::str {
        CREATE ANNOTATION std::description :=
            "Query tag, commonly specifies the origin of the query, e.g 'gel/cli' for queries originating from the CLI.  Clients can specify a tag for easier query identification.";
    };

    CREATE PROPERTY compilation_config -> std::json;
    CREATE PROPERTY protocol_version -> tuple<major: std::int16,
                                              minor: std::int16>;
    CREATE PROPERTY default_namespace -> std::str;
    CREATE OPTIONAL PROPERTY namespace_aliases -> std::json;
    CREATE OPTIONAL PROPERTY output_format -> sys::OutputFormat;
    CREATE OPTIONAL PROPERTY expect_one -> std::bool;
    CREATE OPTIONAL PROPERTY implicit_limit -> std::int64;
    CREATE OPTIONAL PROPERTY inline_typeids -> std::bool;
    CREATE OPTIONAL PROPERTY inline_typenames -> std::bool;
    CREATE OPTIONAL PROPERTY inline_objectids -> std::bool;

    CREATE PROPERTY plans -> std::int64 {
        CREATE ANNOTATION std::description :=
            "Number of times the query was planned in the backend.";
    };
    CREATE PROPERTY total_plan_time -> std::duration {
        CREATE ANNOTATION std::description :=
            "Total time spent planning the query in the backend.";
    };
    CREATE PROPERTY min_plan_time -> std::duration {
        CREATE ANNOTATION std::description :=
            "Minimum time spent planning the query in the backend. "
            ++ "This field will be zero if the counter has been reset "
            ++ "using the `sys::reset_query_stats` function "
            ++ "with the `minmax_only` parameter set to `true` "
            ++ "and never been planned since.";
    };
    CREATE PROPERTY max_plan_time -> std::duration {
        CREATE ANNOTATION std::description :=
            "Maximum time spent planning the query in the backend. "
            ++ "This field will be zero if the counter has been reset "
            ++ "using the `sys::reset_query_stats` function "
            ++ "with the `minmax_only` parameter set to `true` "
            ++ "and never been planned since.";
    };
    CREATE PROPERTY mean_plan_time -> std::duration {
        CREATE ANNOTATION std::description :=
            "Mean time spent planning the query in the backend.";
    };
    CREATE PROPERTY stddev_plan_time -> std::duration {
        CREATE ANNOTATION std::description :=
            "Population standard deviation of time spent "
            ++ "planning the query in the backend.";
    };

    CREATE PROPERTY calls -> std::int64 {
        CREATE ANNOTATION std::description :=
            "Number of times the query was executed.";
    };
    CREATE PROPERTY total_exec_time -> std::duration {
        CREATE ANNOTATION std::description :=
            "Total time spent executing the query in the backend.";
    };
    CREATE PROPERTY min_exec_time -> std::duration {
        CREATE ANNOTATION std::description :=
            "Minimum time spent executing the query in the backend, "
            ++ "this field will be zero until this query is executed "
            ++ "first time after reset performed by the "
            ++ "`sys::reset_query_stats` function with the "
            ++ "`minmax_only` parameter set to `true`";
    };
    CREATE PROPERTY max_exec_time -> std::duration {
        CREATE ANNOTATION std::description :=
            "Maximum time spent executing the query in the backend, "
            ++ "this field will be zero until this query is executed "
            ++ "first time after reset performed by the "
            ++ "`sys::reset_query_stats` function with the "
            ++ "`minmax_only` parameter set to `true`";
    };
    CREATE PROPERTY mean_exec_time -> std::duration {
        CREATE ANNOTATION std::description :=
            "Mean time spent executing the query in the backend.";
    };
    CREATE PROPERTY stddev_exec_time -> std::duration {
        CREATE ANNOTATION std::description :=
            "Population standard deviation of time spent "
            ++ "executing the query in the backend.";
    };

    CREATE PROPERTY rows -> std::int64 {
        CREATE ANNOTATION std::description :=
            "Total number of rows retrieved or affected by the query.";
    };
    CREATE PROPERTY stats_since -> std::datetime {
        CREATE ANNOTATION std::description :=
            "Time at which statistics gathering started for this query.";
    };
    CREATE PROPERTY minmax_stats_since -> std::datetime {
        CREATE ANNOTATION std::description :=
            "Time at which min/max statistics gathering started "
            ++ "for this query (fields `min_plan_time`, `max_plan_time`, "
            ++ "`min_exec_time` and `max_exec_time`).";
    };

    CREATE ACCESS POLICY ap_read allow select using (
        global sys::perm::superuser
    );
};


CREATE FUNCTION
sys::reset_query_stats(
    named only branch_name: OPTIONAL std::str = {},
    named only id: OPTIONAL std::uuid = {},
    named only minmax_only: OPTIONAL std::bool = false,
) -> OPTIONAL std::datetime {
    CREATE ANNOTATION std::description :=
        'Discard query statistics gathered so far corresponding to the '
        ++ 'specified `branch_name` and `id`. If either of the '
        ++ 'parameters is not specified, the statistics that match with the '
        ++ 'other parameter will be reset. If no parameter is specified, '
        ++ 'it will discard all statistics. When `minmax_only` is `true`, '
        ++ 'only the values of minimum and maximum planning and execution '
        ++ 'time will be reset (i.e. `min_plan_time`, `max_plan_time`, '
        ++ '`min_exec_time` and `max_exec_time` fields). The default value '
        ++ 'for `minmax_only` parameter is `false`. This function returns '
        ++ 'the time of a reset. This time is saved to `stats_reset` or '
        ++ '`minmax_stats_since` field of `sys::QueryStats` if the '
        ++ 'corresponding reset was actually performed.';
    SET volatility := 'Volatile';
    USING SQL FUNCTION 'edgedb.reset_query_stats';
    set required_permissions := { sys::perm::superuser };
};


# An intermediate function is needed because we can't
# cast JSON to tuples yet.  DO NOT use directly, it'll go away.
CREATE FUNCTION
sys::__version_internal() -> tuple<major: std::int64,
                                   minor: std::int64,
                                   stage: std::str,
                                   stage_no: std::int64,
                                   local: array<std::str>>
{
    # This function reads from a table.
    SET volatility := 'Stable';
    SET internal := true;
    USING SQL $$
    SELECT
        (v ->> 'major')::int8,
        (v ->> 'minor')::int8,
        (v ->> 'stage')::text,
        (v ->> 'stage_no')::int8,
        (SELECT coalesce(array_agg(el), ARRAY[]::text[])
         FROM jsonb_array_elements_text(v -> 'local') AS el)
    FROM
        (SELECT
            pg_catalog.current_setting('edgedb.server_version')::jsonb AS v
        ) AS q
    $$;
};


CREATE FUNCTION
sys::get_version() -> tuple<major: std::int64,
                            minor: std::int64,
                            stage: sys::VersionStage,
                            stage_no: std::int64,
                            local: array<std::str>>
{
    CREATE ANNOTATION std::description :=
        'Return the server version as a tuple.';
    SET volatility := 'Stable';
    USING (
        SELECT <tuple<major: std::int64,
                    minor: std::int64,
                    stage: sys::VersionStage,
                    stage_no: std::int64,
                    local: array<std::str>>>sys::__version_internal()
    );
};


CREATE FUNCTION
sys::get_version_as_str() -> std::str
{
    CREATE ANNOTATION std::description :=
        'Return the server version as a string.';
    SET volatility := 'Stable';
    USING (
        WITH v := sys::get_version()
        SELECT
            <str>v.major
            ++ '.' ++ <str>v.minor
            ++ (('-' ++ <str>v.stage ++ '.' ++ <str>v.stage_no)
                IF v.stage != <sys::VersionStage>'final' ELSE '')
            ++ (('+' ++ std::array_join(v.local, '.')) IF len(v.local) > 0
                ELSE '')
    );
};


CREATE FUNCTION sys::get_instance_name() -> std::str{
    CREATE ANNOTATION std::description :=
        'Return the server instance name.';
    SET volatility := 'Stable';
    USING SQL $$
        SELECT pg_catalog.current_setting('edgedb.instance_name');
    $$;
};


CREATE FUNCTION
sys::get_transaction_isolation() -> sys::TransactionIsolation
{
    CREATE ANNOTATION std::description :=
        'Return the isolation level of the current transaction.';
    # This function only reads from a table.
    SET volatility := 'Stable';
    SET force_return_cast := true;
    USING SQL FUNCTION 'edgedb._get_transaction_isolation';
};


CREATE FUNCTION
sys::get_current_database() -> str
{
    CREATE ANNOTATION std::description :=
        'Return the name of the current database branch as a string.';
    # The results won't change within a single statement.
    SET volatility := 'Stable';
    USING SQL FUNCTION 'edgedb.get_current_database';
};


CREATE FUNCTION
sys::get_current_branch() -> str
{
    CREATE ANNOTATION std::description :=
        'Return the name of the current database branch as a string.';
    # The results won't change within a single statement.
    SET volatility := 'Stable';
    USING SQL FUNCTION 'edgedb.get_current_database';
};


CREATE FUNCTION
sys::_describe_roles_as_ddl() -> str
{
    # The results won't change within a single statement.
    SET volatility := 'Stable';
    SET internal := true;
    USING SQL FUNCTION 'edgedb._describe_roles_as_ddl';
    set required_permissions := { sys::perm::superuser };
};


CREATE FUNCTION
sys::_get_all_role_memberships(r: uuid) -> array<uuid>
{
    # The results won't change within a single statement.
    SET volatility := 'Stable';
    SET internal := true;
    USING SQL FUNCTION 'edgedb._all_role_memberships';
    set impl_is_strict := false;
    set required_permissions := { sys::perm::superuser };
};


ALTER TYPE sys::Role {
    CREATE MULTI PROPERTY all_permissions := distinct({
        .permissions,
        (
            with self_id := .id
            select detached sys::Role
            filter .id in array_unpack(
                sys::_get_all_role_memberships(self_id)
            )
        ).permissions,
    });
};


CREATE FUNCTION
sys::__pg_and(a: OPTIONAL std::bool, b: OPTIONAL std::bool) -> std::bool
{
    SET volatility := 'Immutable';
    SET internal := true;
    USING SQL $$
        SELECT a AND b;
    $$;
};


CREATE FUNCTION
sys::__pg_or(a: OPTIONAL std::bool, b: OPTIONAL std::bool) -> std::bool
{
    SET volatility := 'Immutable';
    SET internal := true;
    USING SQL $$
        SELECT a OR b;
    $$;
};


CREATE FUNCTION
sys::approximate_count(
    type: schema::ObjectType,
    NAMED ONLY ignore_subtypes: std::bool=false,
) -> int64
{
    SET volatility := 'Stable';
    USING SQL FUNCTION 'edgedb.approximate_count';
    set impl_is_strict := false;
    set required_permissions := { sys::perm::superuser };
};

CREATE REQUIRED GLOBAL sys::current_role -> str {
    SET default := '';
};

# Add permissions to schema and std.

# These modules are populated before sys permissions so we need to
# add these restrictions here.

ALTER TYPE schema::Migration {
    CREATE ACCESS POLICY ap_read allow select using (
        global sys::perm::ddl
    );
};

ALTER FUNCTION std::sequence_reset(
    seq: schema::ScalarType,
    value: std::int64,
) {
    SET required_permissions := sys::perm::ddl;
};
ALTER FUNCTION std::sequence_reset(
    seq: schema::ScalarType,
) {
    SET required_permissions := sys::perm::ddl;
};
