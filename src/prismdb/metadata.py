"""
PRISM-DB Metadata Management

管理meta schema中的所有11张元数据表：
- 参考库（可外链）：params, flags, visits
- Study-specific：study_info, variables, derivations, outputs,
                  output_variables, output_params, functions, dependencies
"""

from typing import Dict, List, Any, Optional
import json
import logging
from .database import Database

logger = logging.getLogger(__name__)


class MetadataManager:
    """元数据管理器 - 管理11张meta表"""

    def __init__(self, db: Database):
        self.db = db

    # ========================================
    # 1. Study Info
    # ========================================

    def set_study_info(
        self,
        study_code: str,
        indication: str = None,
        description: str = None,
        als_version: str = None,
        spec_version: str = None,
    ) -> None:
        sql = """
            INSERT INTO meta.study_info 
            (study_code, indication, description, als_version, spec_version)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (study_code) 
            DO UPDATE SET
                indication = EXCLUDED.indication,
                description = EXCLUDED.description,
                als_version = EXCLUDED.als_version,
                spec_version = EXCLUDED.spec_version,
                updated_at = NOW()
        """
        self.db.execute(
            sql, (study_code, indication, description, als_version, spec_version)
        )
        logger.info(f"Study info set: {study_code}")

    def get_study_info(self) -> Optional[Dict]:
        sql = "SELECT * FROM meta.study_info LIMIT 1"
        result = self.db.query_df(sql)
        if len(result) == 0:
            return None
        return result.iloc[0].to_dict()

    # ========================================
    # 2. Params (参数库 - 可外链)
    # ========================================

    def add_param(
        self,
        param_id: str,
        paramcd: str,
        param_label: str,
        param_desc: str = None,
        category: str = None,
        data_type: str = None,
        unit: str = None,
        default_source_form: str = None,
        default_source_var: str = None,
        default_aval_expr: str = None,
        has_baseline: bool = True,
        baseline_definition: str = None,
        is_external: bool = False,
        external_source: str = None,
        display_order: int = None,
    ) -> None:
        sql = """
            INSERT INTO meta.params
            (param_id, paramcd, param_label, param_desc, category, data_type,
             unit, default_source_form, default_source_var, default_aval_expr,
             has_baseline, baseline_definition, is_external, external_source, display_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (param_id) 
            DO UPDATE SET
                paramcd = EXCLUDED.paramcd,
                param_label = EXCLUDED.param_label,
                param_desc = EXCLUDED.param_desc,
                category = EXCLUDED.category,
                data_type = EXCLUDED.data_type,
                unit = EXCLUDED.unit,
                default_source_form = EXCLUDED.default_source_form,
                default_source_var = EXCLUDED.default_source_var,
                default_aval_expr = EXCLUDED.default_aval_expr,
                has_baseline = EXCLUDED.has_baseline,
                baseline_definition = EXCLUDED.baseline_definition,
                is_external = EXCLUDED.is_external,
                external_source = EXCLUDED.external_source,
                display_order = EXCLUDED.display_order
        """
        self.db.execute(
            sql,
            (
                param_id,
                paramcd,
                param_label,
                param_desc,
                category,
                data_type,
                unit,
                default_source_form,
                default_source_var,
                default_aval_expr,
                has_baseline,
                baseline_definition,
                is_external,
                external_source,
                display_order,
            ),
        )
        logger.info(f"Param added: {paramcd}")

    def get_params(self, category: str = None, is_external: bool = None) -> List[Dict]:
        sql = "SELECT * FROM meta.params WHERE 1=1"
        params = []

        if category:
            sql += " AND category = ?"
            params.append(category)

        if is_external is not None:
            sql += " AND is_external = ?"
            params.append(is_external)

        sql += " ORDER BY display_order NULLS LAST, paramcd"

        df = self.db.query_df(sql, tuple(params) if params else None)
        return df.to_dict("records")

    def get_param_by_code(self, paramcd: str) -> Optional[Dict]:
        sql = "SELECT * FROM meta.params WHERE paramcd = ?"
        df = self.db.query_df(sql, (paramcd,))
        if len(df) == 0:
            return None
        return df.iloc[0].to_dict()

    # ========================================
    # 3. Flags (Flag库 - 可外链)
    # ========================================

    def add_flag(
        self,
        flag_id: str,
        flag_name: str,
        flag_label: str,
        domain: str,
        flag_desc: str = None,
        default_condition: str = None,
        true_value: str = "Y",
        false_value: str = "N",
        is_external: bool = False,
        external_source: str = None,
        display_order: int = None,
    ) -> None:
        sql = """
            INSERT INTO meta.flags
            (flag_id, flag_name, flag_label, flag_desc, domain, default_condition,
             true_value, false_value, is_external, external_source, display_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (flag_id) 
            DO UPDATE SET
                flag_name = EXCLUDED.flag_name,
                flag_label = EXCLUDED.flag_label,
                flag_desc = EXCLUDED.flag_desc,
                domain = EXCLUDED.domain,
                default_condition = EXCLUDED.default_condition,
                true_value = EXCLUDED.true_value,
                false_value = EXCLUDED.false_value,
                is_external = EXCLUDED.is_external,
                external_source = EXCLUDED.external_source,
                display_order = EXCLUDED.display_order
        """
        self.db.execute(
            sql,
            (
                flag_id,
                flag_name,
                flag_label,
                flag_desc,
                domain,
                default_condition,
                true_value,
                false_value,
                is_external,
                external_source,
                display_order,
            ),
        )
        logger.info(f"Flag added: {flag_name}")

    def get_flags(self, domain: str = None, is_external: bool = None) -> List[Dict]:
        sql = "SELECT * FROM meta.flags WHERE 1=1"
        params = []

        if domain:
            sql += " AND domain = ?"
            params.append(domain)

        if is_external is not None:
            sql += " AND is_external = ?"
            params.append(is_external)

        sql += " ORDER BY display_order NULLS LAST, flag_name"

        df = self.db.query_df(sql, tuple(params) if params else None)
        return df.to_dict("records")

    # ========================================
    # 4. Visits (Analysis Visit库)
    # ========================================

    def add_visit(
        self,
        visit_id: str,
        visit_name: str,
        visitnum: int = None,
        visit_label: str = None,
        visit_type: str = None,
        is_baseline: bool = False,
        is_endpoint: bool = False,
        target_day: int = None,
        window_lower: int = None,
        window_upper: int = None,
        is_external: bool = False,
        external_source: str = None,
        display_order: int = None,
    ) -> None:
        sql = """
            INSERT INTO meta.visits
            (visit_id, visitnum, visit_name, visit_label, visit_type,
             is_baseline, is_endpoint, target_day, window_lower, window_upper,
             is_external, external_source, display_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (visit_id) 
            DO UPDATE SET
                visitnum = EXCLUDED.visitnum,
                visit_name = EXCLUDED.visit_name,
                visit_label = EXCLUDED.visit_label,
                visit_type = EXCLUDED.visit_type,
                is_baseline = EXCLUDED.is_baseline,
                is_endpoint = EXCLUDED.is_endpoint,
                target_day = EXCLUDED.target_day,
                window_lower = EXCLUDED.window_lower,
                window_upper = EXCLUDED.window_upper,
                is_external = EXCLUDED.is_external,
                external_source = EXCLUDED.external_source,
                display_order = EXCLUDED.display_order
        """
        self.db.execute(
            sql,
            (
                visit_id,
                visitnum,
                visit_name,
                visit_label,
                visit_type,
                is_baseline,
                is_endpoint,
                target_day,
                window_lower,
                window_upper,
                is_external,
                external_source,
                display_order,
            ),
        )
        logger.info(f"Visit added: {visit_name}")

    def get_visits(
        self, is_baseline: bool = None, is_endpoint: bool = None
    ) -> List[Dict]:
        sql = "SELECT * FROM meta.visits WHERE 1=1"
        params = []

        if is_baseline is not None:
            sql += " AND is_baseline = ?"
            params.append(is_baseline)

        if is_endpoint is not None:
            sql += " AND is_endpoint = ?"
            params.append(is_endpoint)

        sql += " ORDER BY visitnum NULLS LAST, display_order NULLS LAST"

        df = self.db.query_df(sql, tuple(params) if params else None)
        return df.to_dict("records")

    # ========================================
    # 5. Variables (变量表)
    # ========================================

    def add_variable(
        self,
        var_id: str,
        var_name: str,
        schema: str,
        var_label: str = None,
        block: str = None,
        data_type: str = None,
        param_ref: str = None,
        flag_ref: str = None,
        is_baseline_of_param: bool = False,
        display_order: int = None,
    ) -> None:
        sql = """
            INSERT INTO meta.variables
            (var_id, var_name, var_label, schema, block, data_type,
             param_ref, flag_ref, is_baseline_of_param, display_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (var_id) 
            DO UPDATE SET
                var_name = EXCLUDED.var_name,
                var_label = EXCLUDED.var_label,
                schema = EXCLUDED.schema,
                block = EXCLUDED.block,
                data_type = EXCLUDED.data_type,
                param_ref = EXCLUDED.param_ref,
                flag_ref = EXCLUDED.flag_ref,
                is_baseline_of_param = EXCLUDED.is_baseline_of_param,
                display_order = EXCLUDED.display_order
        """
        self.db.execute(
            sql,
            (
                var_id,
                var_name,
                var_label,
                schema,
                block,
                data_type,
                param_ref,
                flag_ref,
                is_baseline_of_param,
                display_order,
            ),
        )
        logger.info(f"Variable added: {var_id} ({schema})")

    def get_variables(
        self,
        schema: str = None,
        block: str = None,
        param_ref: str = None,
        flag_ref: str = None,
    ) -> List[Dict]:
        sql = "SELECT * FROM meta.variables WHERE 1=1"
        params = []

        if schema:
            sql += " AND schema = ?"
            params.append(schema)

        if block:
            sql += " AND block = ?"
            params.append(block)

        if param_ref:
            sql += " AND param_ref = ?"
            params.append(param_ref)

        if flag_ref:
            sql += " AND flag_ref = ?"
            params.append(flag_ref)

        sql += " ORDER BY schema, block NULLS LAST, display_order NULLS LAST, var_id"

        df = self.db.query_df(sql, tuple(params) if params else None)
        return df.to_dict("records")

    def get_variable(self, var_id: str) -> Optional[Dict]:
        sql = "SELECT * FROM meta.variables WHERE var_id = ?"
        df = self.db.query_df(sql, (var_id,))
        if len(df) == 0:
            return None
        return df.iloc[0].to_dict()

    # ========================================
    # 6. Derivations (衍生规则)
    # ========================================

    def add_derivation(
        self,
        deriv_id: str,
        target_var: str,
        transformation: str,
        source_vars: List[str] = None,
        source_tables: List[str] = None,
        transformation_type: str = None,
        function_id: str = None,
        rule_doc_path: str = None,
        complexity: str = None,
        description: str = None,
    ) -> None:
        source_vars_json = json.dumps(source_vars) if source_vars else None
        source_tables_json = json.dumps(source_tables) if source_tables else None

        sql = """
            INSERT INTO meta.derivations
            (deriv_id, target_var, source_vars, source_tables, transformation,
             transformation_type, function_id, rule_doc_path, complexity, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (deriv_id) 
            DO UPDATE SET
                target_var = EXCLUDED.target_var,
                source_vars = EXCLUDED.source_vars,
                source_tables = EXCLUDED.source_tables,
                transformation = EXCLUDED.transformation,
                transformation_type = EXCLUDED.transformation_type,
                function_id = EXCLUDED.function_id,
                rule_doc_path = EXCLUDED.rule_doc_path,
                complexity = EXCLUDED.complexity,
                description = EXCLUDED.description
        """
        self.db.execute(
            sql,
            (
                deriv_id,
                target_var,
                source_vars_json,
                source_tables_json,
                transformation,
                transformation_type,
                function_id,
                rule_doc_path,
                complexity,
                description,
            ),
        )
        logger.info(f"Derivation added: {deriv_id}")

    def get_derivations(
        self, complexity: str = None, transformation_type: str = None
    ) -> List[Dict]:
        sql = "SELECT * FROM meta.derivations WHERE 1=1"
        params = []

        if complexity:
            sql += " AND complexity = ?"
            params.append(complexity)

        if transformation_type:
            sql += " AND transformation_type = ?"
            params.append(transformation_type)

        sql += " ORDER BY complexity, deriv_id"

        df = self.db.query_df(sql, tuple(params) if params else None)
        return df.to_dict("records")

    def get_derivation_for_var(self, var_id: str) -> Optional[Dict]:
        sql = "SELECT * FROM meta.derivations WHERE target_var = ?"
        df = self.db.query_df(sql, (var_id,))
        if len(df) == 0:
            return None
        return df.iloc[0].to_dict()

    # ========================================
    # 7. Outputs (输出定义)
    # ========================================

    def add_output(
        self,
        output_id: str,
        output_type: str,
        schema: str,
        title: str = None,
        source_block: str = None,
        population: str = None,
        visit_filter: str = None,
        filter_expr: str = None,
        render_function: str = None,
        render_options: Dict = None,
        section: str = None,
        display_order: int = None,
    ) -> None:
        render_options_json = json.dumps(render_options) if render_options else None

        sql = """
            INSERT INTO meta.outputs
            (output_id, output_type, title, schema, source_block,
             population, visit_filter, filter_expr, render_function,
             render_options, section, display_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (output_id) 
            DO UPDATE SET
                output_type = EXCLUDED.output_type,
                title = EXCLUDED.title,
                schema = EXCLUDED.schema,
                source_block = EXCLUDED.source_block,
                population = EXCLUDED.population,
                visit_filter = EXCLUDED.visit_filter,
                filter_expr = EXCLUDED.filter_expr,
                render_function = EXCLUDED.render_function,
                render_options = EXCLUDED.render_options,
                section = EXCLUDED.section,
                display_order = EXCLUDED.display_order
        """
        self.db.execute(
            sql,
            (
                output_id,
                output_type,
                title,
                schema,
                source_block,
                population,
                visit_filter,
                filter_expr,
                render_function,
                render_options_json,
                section,
                display_order,
            ),
        )
        logger.info(f"Output added: {output_id}")

    def get_outputs(
        self, schema: str = None, output_type: str = None, section: str = None
    ) -> List[Dict]:
        sql = "SELECT * FROM meta.outputs WHERE 1=1"
        params = []

        if schema:
            sql += " AND schema = ?"
            params.append(schema)

        if output_type:
            sql += " AND output_type = ?"
            params.append(output_type)

        if section:
            sql += " AND section = ?"
            params.append(section)

        sql += " ORDER BY section NULLS LAST, display_order NULLS LAST, output_id"

        df = self.db.query_df(sql, tuple(params) if params else None)
        return df.to_dict("records")

    def get_output(self, output_id: str) -> Optional[Dict]:
        sql = "SELECT * FROM meta.outputs WHERE output_id = ?"
        df = self.db.query_df(sql, (output_id,))
        if len(df) == 0:
            return None
        return df.iloc[0].to_dict()

    # ========================================
    # 8. Output Variables (输出-变量关联)
    # ========================================

    def add_output_variable(
        self,
        output_id: str,
        var_id: str,
        role: str = None,
        display_label: str = None,
        display_order: int = None,
    ) -> None:
        sql = """
            INSERT INTO meta.output_variables
            (output_id, var_id, role, display_label, display_order)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (output_id, var_id) 
            DO UPDATE SET
                role = EXCLUDED.role,
                display_label = EXCLUDED.display_label,
                display_order = EXCLUDED.display_order
        """
        self.db.execute(sql, (output_id, var_id, role, display_label, display_order))
        logger.info(f"Output variable added: {output_id} -> {var_id}")

    def get_output_variables(self, output_id: str) -> List[Dict]:
        sql = """
            SELECT ov.*, v.var_name, v.var_label, v.schema, v.data_type
            FROM meta.output_variables ov
            JOIN meta.variables v ON ov.var_id = v.var_id
            WHERE ov.output_id = ?
            ORDER BY ov.display_order NULLS LAST
        """
        df = self.db.query_df(sql, (output_id,))
        return df.to_dict("records")

    # ========================================
    # 9. Output Params (输出-参数关联)
    # ========================================

    def add_output_param(
        self, output_id: str, paramcd: str, display_order: int = None
    ) -> None:
        sql = """
            INSERT INTO meta.output_params
            (output_id, paramcd, display_order)
            VALUES (?, ?, ?)
            ON CONFLICT (output_id, paramcd) 
            DO UPDATE SET
                display_order = EXCLUDED.display_order
        """
        self.db.execute(sql, (output_id, paramcd, display_order))
        logger.info(f"Output param added: {output_id} -> {paramcd}")

    def get_output_params(self, output_id: str) -> List[Dict]:
        sql = """
            SELECT op.*, p.param_label, p.category, p.unit
            FROM meta.output_params op
            JOIN meta.params p ON op.paramcd = p.paramcd
            WHERE op.output_id = ?
            ORDER BY op.display_order NULLS LAST
        """
        df = self.db.query_df(sql, (output_id,))
        return df.to_dict("records")

    # ========================================
    # 10. Functions (函数库)
    # ========================================

    def add_function(
        self,
        function_id: str,
        function_name: str,
        impl_type: str,
        description: str = None,
        impl_code: str = None,
        input_params: Dict = None,
        output_type: str = None,
    ) -> None:
        input_params_json = json.dumps(input_params) if input_params else None

        sql = """
            INSERT INTO meta.functions
            (function_id, function_name, description, impl_type, impl_code,
             input_params, output_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (function_id) 
            DO UPDATE SET
                function_name = EXCLUDED.function_name,
                description = EXCLUDED.description,
                impl_type = EXCLUDED.impl_type,
                impl_code = EXCLUDED.impl_code,
                input_params = EXCLUDED.input_params,
                output_type = EXCLUDED.output_type
        """
        self.db.execute(
            sql,
            (
                function_id,
                function_name,
                description,
                impl_type,
                impl_code,
                input_params_json,
                output_type,
            ),
        )
        logger.info(f"Function added: {function_id}")

    def get_functions(self, impl_type: str = None) -> List[Dict]:
        sql = "SELECT * FROM meta.functions WHERE 1=1"
        params = []

        if impl_type:
            sql += " AND impl_type = ?"
            params.append(impl_type)

        sql += " ORDER BY function_id"

        df = self.db.query_df(sql, tuple(params) if params else None)
        return df.to_dict("records")

    def get_function(self, function_id: str) -> Optional[Dict]:
        sql = "SELECT * FROM meta.functions WHERE function_id = ?"
        df = self.db.query_df(sql, (function_id,))
        if len(df) == 0:
            return None
        return df.iloc[0].to_dict()

    # ========================================
    # 11. Dependencies (依赖关系)
    # ========================================

    def add_dependency(self, from_var: str, to_var: str) -> None:
        sql = """
            INSERT INTO meta.dependencies (from_var, to_var)
            VALUES (?, ?)
            ON CONFLICT (from_var, to_var) DO NOTHING
        """
        self.db.execute(sql, (from_var, to_var))
        logger.info(f"Dependency added: {from_var} -> {to_var}")

    def get_dependencies(self, var_id: str = None) -> List[Dict]:
        sql = "SELECT * FROM meta.dependencies WHERE 1=1"
        params = []

        if var_id:
            sql += " AND (from_var = ? OR to_var = ?)"
            params.extend([var_id, var_id])

        df = self.db.query_df(sql, tuple(params) if params else None)
        return df.to_dict("records")

    def get_dependents(self, var_id: str) -> List[str]:
        sql = "SELECT from_var FROM meta.dependencies WHERE to_var = ?"
        df = self.db.query_df(sql, (var_id,))
        return df["from_var"].tolist() if len(df) > 0 else []

    def get_dependencies_of(self, var_id: str) -> List[str]:
        sql = "SELECT to_var FROM meta.dependencies WHERE from_var = ?"
        df = self.db.query_df(sql, (var_id,))
        return df["to_var"].tolist() if len(df) > 0 else []

    # ========================================
    # Utility Methods
    # ========================================

    def get_execution_order(self) -> List[str]:
        """
        拓扑排序：获取变量的执行顺序
        返回按依赖关系排序的var_id列表
        """
        deps = self.get_dependencies()
        if not deps:
            variables = self.get_variables()
            return [v["var_id"] for v in variables]

        graph = {}
        in_degree = {}

        for v in self.get_variables():
            var_id = v["var_id"]
            graph[var_id] = []
            in_degree[var_id] = 0

        for d in deps:
            from_var = d["from_var"]
            to_var = d["to_var"]
            if from_var in graph and to_var in graph:
                graph[from_var].append(to_var)
                in_degree[to_var] += 1

        queue = [v for v in in_degree if in_degree[v] == 0]
        result = []

        while queue:
            var = queue.pop(0)
            result.append(var)
            for neighbor in graph.get(var, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return result

    def get_missing_derivations(self) -> List[Dict]:
        sql = """
            SELECT v.* 
            FROM meta.variables v
            LEFT JOIN meta.derivations d ON v.var_id = d.target_var
            WHERE d.deriv_id IS NULL
            ORDER BY v.schema, v.var_id
        """
        df = self.db.query_df(sql)
        return df.to_dict("records")

    def get_output_full_spec(self, output_id: str) -> Optional[Dict]:
        output = self.get_output(output_id)
        if not output:
            return None

        output["variables"] = self.get_output_variables(output_id)
        output["params"] = self.get_output_params(output_id)

        return output
