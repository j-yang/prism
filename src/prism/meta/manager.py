from typing import Dict, List, Any, Optional
import json
import logging
from prism.core.database import Database

logger = logging.getLogger(__name__)


class MetadataManager:
    def __init__(self, db: Database):
        self.db = db

    def set_study_info(
        self,
        study_code: str,
        indication: Optional[str] = None,
        description: Optional[str] = None,
        als_version: Optional[str] = None,
        spec_version: Optional[str] = None,
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

    # ============================================================================
    # Bronze Dictionary
    # ============================================================================

    def add_bronze_variable(
        self,
        var_id: str,
        form_oid: str,
        field_oid: str,
        var_name: str = None,
        var_label: str = None,
        data_type: str = None,
        is_required: bool = False,
        codelist_ref: str = None,
    ) -> None:
        sql = """
            INSERT INTO meta.bronze_dictionary
            (var_id, form_oid, field_oid, var_name, var_label, data_type,
             is_required, codelist_ref)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (var_id)
            DO UPDATE SET
                form_oid = EXCLUDED.form_oid,
                field_oid = EXCLUDED.field_oid,
                var_name = EXCLUDED.var_name,
                var_label = EXCLUDED.var_label,
                data_type = EXCLUDED.data_type,
                is_required = EXCLUDED.is_required,
                codelist_ref = EXCLUDED.codelist_ref
        """
        self.db.execute(
            sql,
            (
                var_id,
                form_oid,
                field_oid,
                var_name,
                var_label,
                data_type,
                is_required,
                codelist_ref,
            ),
        )
        logger.info(f"Bronze variable added: {var_id}")

    def get_bronze_variables(self, form_oid: str = None) -> List[Dict]:
        sql = "SELECT * FROM meta.bronze_dictionary WHERE 1=1"
        params = []

        if form_oid:
            sql += " AND form_oid = ?"
            params.append(form_oid)

        sql += " ORDER BY var_id"

        df = self.db.query_df(sql, tuple(params) if params else None)
        return df.to_dict("records")

    # ============================================================================
    # Silver Dictionary
    # ============================================================================

    def add_silver_variable(
        self,
        var_name: str,
        schema: str,
        var_label: str = None,
        data_type: str = None,
        source_vars: str = None,
        transformation: str = None,
        transformation_type: str = None,
        rule_doc_path: str = None,
        description: str = None,
        param_ref: str = None,
        display_order: int = None,
    ) -> None:
        sql = """
            INSERT INTO meta.silver_dictionary
            (var_name, var_label, schema, data_type, source_vars,
             transformation, transformation_type, rule_doc_path, description,
             param_ref, display_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (var_name)
            DO UPDATE SET
                var_label = EXCLUDED.var_label,
                schema = EXCLUDED.schema,
                data_type = EXCLUDED.data_type,
                source_vars = EXCLUDED.source_vars,
                transformation = EXCLUDED.transformation,
                transformation_type = EXCLUDED.transformation_type,
                rule_doc_path = EXCLUDED.rule_doc_path,
                description = EXCLUDED.description,
                param_ref = EXCLUDED.param_ref,
                display_order = EXCLUDED.display_order
        """
        self.db.execute(
            sql,
            (
                var_name,
                var_label,
                schema,
                data_type,
                source_vars,
                transformation,
                transformation_type,
                rule_doc_path,
                description,
                param_ref,
                display_order,
            ),
        )
        logger.info(f"Silver variable added: {var_name}")

    def get_silver_variables(
        self, schema: str = None, param_ref: str = None
    ) -> List[Dict]:
        sql = "SELECT * FROM meta.silver_dictionary WHERE 1=1"
        params = []

        if schema:
            sql += " AND schema = ?"
            params.append(schema)

        if param_ref:
            sql += " AND param_ref = ?"
            params.append(param_ref)

        sql += " ORDER BY display_order NULLS LAST, var_name"

        df = self.db.query_df(sql, tuple(params) if params else None)
        return df.to_dict("records")

    def get_silver_variable(self, var_name: str) -> Optional[Dict]:
        sql = "SELECT * FROM meta.silver_dictionary WHERE var_name = ?"
        df = self.db.query_df(sql, (var_name,))
        if len(df) == 0:
            return None
        return df.iloc[0].to_dict()

    # ============================================================================
    # Gold Dictionary
    # ============================================================================

    def add_gold_variable(
        self,
        var_id: str,
        group_id: str,
        schema: str,
        population: str = None,
        selection: str = None,
        statistics: List = None,
        deliverable_id: str = None,
        description: str = None,
        unit: str = None,
        display_order: int = None,
    ) -> None:
        statistics_json = json.dumps(statistics) if statistics else None

        sql = """
            INSERT INTO meta.gold_dictionary
            (var_id, group_id, schema, population, selection,
             statistics, deliverable_id, description, unit, display_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (var_id)
            DO UPDATE SET
                group_id = EXCLUDED.group_id,
                schema = EXCLUDED.schema,
                population = EXCLUDED.population,
                selection = EXCLUDED.selection,
                statistics = EXCLUDED.statistics,
                deliverable_id = EXCLUDED.deliverable_id,
                description = EXCLUDED.description,
                unit = EXCLUDED.unit,
                display_order = EXCLUDED.display_order
        """
        self.db.execute(
            sql,
            (
                var_id,
                group_id,
                schema,
                population,
                selection,
                statistics_json,
                deliverable_id,
                description,
                unit,
                display_order,
            ),
        )
        logger.info(f"Gold variable added: {var_id}")

    def get_gold_variables(
        self, schema: str = None, group_id: str = None, deliverable_id: str = None
    ) -> List[Dict]:
        sql = "SELECT * FROM meta.gold_dictionary WHERE 1=1"
        params = []

        if schema:
            sql += " AND schema = ?"
            params.append(schema)

        if group_id:
            sql += " AND group_id = ?"
            params.append(group_id)

        if deliverable_id:
            sql += " AND deliverable_id = ?"
            params.append(deliverable_id)

        sql += " ORDER BY display_order NULLS LAST, var_id"

        df = self.db.query_df(sql, tuple(params) if params else None)
        results = df.to_dict("records")

        # Parse JSON fields
        for r in results:
            if r.get("statistics"):
                r["statistics"] = json.loads(r["statistics"])

        return results

    def get_gold_variable(self, var_id: str) -> Optional[Dict]:
        sql = "SELECT * FROM meta.gold_dictionary WHERE var_id = ?"
        df = self.db.query_df(sql, (var_id,))
        if len(df) == 0:
            return None

        result = df.iloc[0].to_dict()
        if result.get("statistics"):
            result["statistics"] = json.loads(result["statistics"])

        return result

    # ============================================================================
    # Platinum Dictionary
    # ============================================================================

    def add_platinum_deliverable(
        self,
        deliverable_id: str,
        deliverable_type: str,
        title: str = None,
        schema: str = None,
        elements: List = None,
        population: str = None,
        render_function: str = None,
        render_options: Dict = None,
        section: str = None,
        display_order: int = None,
    ) -> None:
        elements_json = json.dumps(elements) if elements else None
        render_options_json = json.dumps(render_options) if render_options else None

        sql = """
            INSERT INTO meta.platinum_dictionary
            (deliverable_id, deliverable_type, title, schema, elements,
             population, render_function, render_options, section, display_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (deliverable_id)
            DO UPDATE SET
                deliverable_type = EXCLUDED.deliverable_type,
                title = EXCLUDED.title,
                schema = EXCLUDED.schema,
                elements = EXCLUDED.elements,
                population = EXCLUDED.population,
                render_function = EXCLUDED.render_function,
                render_options = EXCLUDED.render_options,
                section = EXCLUDED.section,
                display_order = EXCLUDED.display_order
        """
        self.db.execute(
            sql,
            (
                deliverable_id,
                deliverable_type,
                title,
                schema,
                elements_json,
                population,
                render_function,
                render_options_json,
                section,
                display_order,
            ),
        )
        logger.info(f"Platinum deliverable added: {deliverable_id}")

    def get_platinum_deliverables(
        self, schema: str = None, deliverable_type: str = None, section: str = None
    ) -> List[Dict]:
        sql = "SELECT * FROM meta.platinum_dictionary WHERE 1=1"
        params = []

        if schema:
            sql += " AND schema = ?"
            params.append(schema)

        if deliverable_type:
            sql += " AND deliverable_type = ?"
            params.append(deliverable_type)

        if section:
            sql += " AND section = ?"
            params.append(section)

        sql += " ORDER BY section NULLS LAST, display_order NULLS LAST, deliverable_id"

        df = self.db.query_df(sql, tuple(params) if params else None)
        results = df.to_dict("records")

        # Parse JSON fields
        for r in results:
            if r.get("elements"):
                r["elements"] = json.loads(r["elements"])
            if r.get("render_options"):
                r["render_options"] = json.loads(r["render_options"])

        return results

    def get_platinum_deliverable(self, deliverable_id: str) -> Optional[Dict]:
        sql = "SELECT * FROM meta.platinum_dictionary WHERE deliverable_id = ?"
        df = self.db.query_df(sql, (deliverable_id,))
        if len(df) == 0:
            return None

        result = df.iloc[0].to_dict()

        if result.get("elements"):
            result["elements"] = json.loads(result["elements"])
        if result.get("render_options"):
            result["render_options"] = json.loads(result["render_options"])

        return result

    # ============================================================================
    # Form Classification
    # ============================================================================

    def add_form_classification(
        self,
        form_oid: str,
        schema: str,
        domain: Optional[str] = None,
        source_forms: Optional[List[str]] = None,
        confidence: str = "medium",
    ) -> None:
        source_forms_json = json.dumps(source_forms) if source_forms else None

        sql = """
            INSERT INTO meta.form_classification
            (form_oid, domain, schema, source_forms, classification_confidence)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (form_oid)
            DO UPDATE SET
                domain = EXCLUDED.domain,
                schema = EXCLUDED.schema,
                source_forms = EXCLUDED.source_forms,
                classification_confidence = EXCLUDED.classification_confidence
        """
        self.db.execute(sql, (form_oid, domain, schema, source_forms_json, confidence))
        logger.info(f"Form classification added: {form_oid} -> {schema}")

    def get_form_classification(
        self, form_oid: str = None, schema: str = None
    ) -> List[Dict]:
        sql = "SELECT * FROM meta.form_classification WHERE 1=1"
        params = []

        if form_oid:
            sql += " AND form_oid = ?"
            params.append(form_oid)

        if schema:
            sql += " AND schema = ?"
            params.append(schema)

        sql += " ORDER BY schema, form_oid"

        df = self.db.query_df(sql, tuple(params) if params else None)
        results = df.to_dict("records")

        # Parse JSON fields
        for r in results:
            if r.get("source_forms"):
                r["source_forms"] = json.loads(r["source_forms"])

        return results

    def get_forms_by_domain(self, domain: str) -> List[str]:
        sql = "SELECT form_oid FROM meta.form_classification WHERE domain = ?"
        df = self.db.query_df(sql, (domain,))
        return df["form_oid"].tolist() if len(df) > 0 else []

    # ============================================================================
    # Dependencies
    # ============================================================================

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
