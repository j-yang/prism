"""
PRISM-DB Metadata Management
管理meta schema中的所有元数据表
"""
from typing import Dict, List, Any, Optional
import json
import logging
from datetime import datetime
from .database import Database

logger = logging.getLogger(__name__)


class MetadataManager:
    """元数据管理器"""
    
    def __init__(self, db: Database):
        """
        初始化元数据管理器
        
        Args:
            db: Database对象
        """
        self.db = db
    
    # ========================================
    # Schema Docs
    # ========================================
    
    def add_schema_doc(self, layer: str, table_name: str, column_name: str,
                       data_type: str, description: str = None,
                       source: str = None, example_values: List[str] = None):
        """
        添加schema文档记录
        
        Args:
            layer: 层级 ('bronze', 'silver', 'gold')
            table_name: 表名
            column_name: 列名
            data_type: 数据类型
            description: 描述
            source: 来源
            example_values: 示例值列表
        """
        example_json = json.dumps(example_values) if example_values else None
        
        sql = """
            INSERT INTO meta.schema_docs 
            (layer, table_name, column_name, data_type, description, source, example_values)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (layer, table_name, column_name) 
            DO UPDATE SET
                data_type = EXCLUDED.data_type,
                description = EXCLUDED.description,
                source = EXCLUDED.source,
                example_values = EXCLUDED.example_values,
                updated_at = NOW()
        """
        
        self.db.execute(sql, (layer, table_name, column_name, data_type,
                             description, source, example_json))
        logger.info(f"Schema doc added: {layer}.{table_name}.{column_name}")
    
    def get_schema_docs(self, layer: str = None, table_name: str = None) -> List[Dict]:
        """
        查询schema文档
        
        Args:
            layer: 层级（可选）
            table_name: 表名（可选）
            
        Returns:
            Schema文档列表
        """
        sql = "SELECT * FROM meta.schema_docs WHERE 1=1"
        params = []
        
        if layer:
            sql += " AND layer = ?"
            params.append(layer)
        
        if table_name:
            sql += " AND table_name = ?"
            params.append(table_name)
        
        sql += " ORDER BY layer, table_name, column_name"
        
        df = self.db.query_df(sql, tuple(params) if params else None)
        return df.to_dict('records')
    
    # ========================================
    # Data Catalog
    # ========================================
    
    def add_variable(self, var_name: str, schema: str, layer: str,
                    label: str = None, data_type: str = None,
                    source_form: str = None, source_field: str = None,
                    codelist: Dict = None, is_derived: bool = False,
                    derivation_id: str = None, study_code: str = ''):
        """
        添加变量到data catalog
        
        Args:
            var_name: 变量名
            schema: Schema类型 ('baseline', 'longitudinal', 'occurrence')
            layer: 层级 ('bronze', 'silver')
            label: 标签
            data_type: 数据类型
            source_form: 来源form
            source_field: 来源field
            codelist: 代码列表字典
            is_derived: 是否衍生变量
            derivation_id: 衍生规则ID
            study_code: 研究代码 (默认'' 表示cross-study)
        """
        codelist_json = json.dumps(codelist) if codelist else None
        
        sql = """
            INSERT INTO meta.data_catalog
            (var_name, schema, layer, label, data_type, source_form, source_field,
             codelist, is_derived, derivation_id, study_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (var_name, schema, layer, study_code)
            DO UPDATE SET
                label = EXCLUDED.label,
                data_type = EXCLUDED.data_type,
                source_form = EXCLUDED.source_form,
                source_field = EXCLUDED.source_field,
                codelist = EXCLUDED.codelist,
                is_derived = EXCLUDED.is_derived,
                derivation_id = EXCLUDED.derivation_id,
                updated_at = NOW()
        """
        
        self.db.execute(sql, (var_name, schema, layer, label, data_type,
                             source_form, source_field, codelist_json,
                             is_derived, derivation_id, study_code))
        logger.info(f"Variable added to catalog: {var_name} ({schema}.{layer})")
    
    def get_variables(self, schema: str = None, layer: str = None,
                     study_code: str = None, is_derived: bool = None) -> List[Dict]:
        """
        查询变量目录
        
        Args:
            schema: Schema类型（可选）
            layer: 层级（可选）
            study_code: 研究代码（可选）
            is_derived: 是否衍生变量（可选）
            
        Returns:
            变量列表
        """
        sql = "SELECT * FROM meta.data_catalog WHERE 1=1"
        params = []
        
        if schema:
            sql += " AND schema = ?"
            params.append(schema)
        
        if layer:
            sql += " AND layer = ?"
            params.append(layer)
        
        if study_code:
            sql += " AND study_code = ?"
            params.append(study_code)
        
        if is_derived is not None:
            sql += " AND is_derived = ?"
            params.append(is_derived)
        
        sql += " ORDER BY schema, layer, var_name"
        
        df = self.db.query_df(sql, tuple(params) if params else None)
        return df.to_dict('records')
    
    # ========================================
    # Derivations
    # ========================================
    
    def add_derivation(self, derivation_id: str, target_var: str, target_schema: str,
                      transformation_sql: str, depends_on: List[str] = None,
                      complexity: str = 'simple', description: str = None,
                      rule_doc: str = None, study_overrides: Dict = None,
                      execution_order: int = None):
        """
        添加衍生规则
        
        Args:
            derivation_id: 衍生规则ID
            target_var: 目标变量
            target_schema: 目标schema
            transformation_sql: 转换SQL
            depends_on: 依赖变量列表
            complexity: 复杂度 ('simple', 'medium', 'complex')
            description: 描述
            rule_doc: 规则文档路径
            study_overrides: Study特定覆盖
            execution_order: 执行顺序
        """
        depends_json = json.dumps(depends_on) if depends_on else None
        overrides_json = json.dumps(study_overrides) if study_overrides else None
        
        sql = """
            INSERT INTO meta.derivations
            (derivation_id, target_var, target_schema, transformation_sql,
             depends_on, complexity, description, rule_doc, study_overrides,
             execution_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (derivation_id)
            DO UPDATE SET
                target_var = EXCLUDED.target_var,
                target_schema = EXCLUDED.target_schema,
                transformation_sql = EXCLUDED.transformation_sql,
                depends_on = EXCLUDED.depends_on,
                complexity = EXCLUDED.complexity,
                description = EXCLUDED.description,
                rule_doc = EXCLUDED.rule_doc,
                study_overrides = EXCLUDED.study_overrides,
                execution_order = EXCLUDED.execution_order,
                updated_at = NOW()
        """
        
        self.db.execute(sql, (derivation_id, target_var, target_schema,
                             transformation_sql, depends_json, complexity,
                             description, rule_doc, overrides_json, execution_order))
        logger.info(f"Derivation added: {derivation_id}")
    
    def get_derivations(self, target_schema: str = None, 
                       is_active: bool = True) -> List[Dict]:
        """
        查询衍生规则
        
        Args:
            target_schema: 目标schema（可选）
            is_active: 是否激活（可选）
            
        Returns:
            衍生规则列表
        """
        sql = "SELECT * FROM meta.derivations WHERE 1=1"
        params = []
        
        if target_schema:
            sql += " AND target_schema = ?"
            params.append(target_schema)
        
        if is_active is not None:
            sql += " AND is_active = ?"
            params.append(is_active)
        
        sql += " ORDER BY execution_order NULLS LAST, derivation_id"
        
        df = self.db.query_df(sql, tuple(params) if params else None)
        return df.to_dict('records')
    
    # ========================================
    # Output Spec
    # ========================================
    
    def add_output_spec(self, output_id: str, output_type: str, schema: str,
                       source_table: str = None, required_vars: List[str] = None,
                       required_params: List[str] = None, filter_condition: str = None,
                       group_by: Dict = None, comparison: str = None,
                       stats_required: List[str] = None, analysis_method: str = None,
                       analysis_spec: Dict = None, title_template: str = None,
                       footnote_template: str = None, study_overrides: Dict = None,
                       block: str = None, sort_order: int = None):
        """
        添加输出定义
        
        Args:
            output_id: 输出ID
            output_type: 输出类型
            schema: Schema类型
            source_table: 来源表
            required_vars: 需要的变量列表
            required_params: 需要的参数列表
            filter_condition: 筛选条件
            group_by: 分组配置
            comparison: 比较类型
            stats_required: 需要的统计量
            analysis_method: 分析方法
            analysis_spec: 分析规格
            title_template: 标题模板
            footnote_template: 脚注模板
            study_overrides: Study特定覆盖
            block: 区块
            sort_order: 排序
        """
        vars_json = json.dumps(required_vars) if required_vars else None
        params_json = json.dumps(required_params) if required_params else None
        group_json = json.dumps(group_by) if group_by else None
        stats_json = json.dumps(stats_required) if stats_required else None
        spec_json = json.dumps(analysis_spec) if analysis_spec else None
        overrides_json = json.dumps(study_overrides) if study_overrides else None
        
        sql = """
            INSERT INTO meta.output_spec
            (output_id, output_type, schema, source_table, required_vars,
             required_params, filter_condition, group_by, comparison,
             stats_required, analysis_method, analysis_spec,
             title_template, footnote_template, study_overrides,
             block, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (output_id)
            DO UPDATE SET
                output_type = EXCLUDED.output_type,
                schema = EXCLUDED.schema,
                source_table = EXCLUDED.source_table,
                required_vars = EXCLUDED.required_vars,
                required_params = EXCLUDED.required_params,
                filter_condition = EXCLUDED.filter_condition,
                group_by = EXCLUDED.group_by,
                comparison = EXCLUDED.comparison,
                stats_required = EXCLUDED.stats_required,
                analysis_method = EXCLUDED.analysis_method,
                analysis_spec = EXCLUDED.analysis_spec,
                title_template = EXCLUDED.title_template,
                footnote_template = EXCLUDED.footnote_template,
                study_overrides = EXCLUDED.study_overrides,
                block = EXCLUDED.block,
                sort_order = EXCLUDED.sort_order,
                updated_at = NOW()
        """
        
        self.db.execute(sql, (output_id, output_type, schema, source_table,
                             vars_json, params_json, filter_condition, group_json,
                             comparison, stats_json, analysis_method, spec_json,
                             title_template, footnote_template, overrides_json,
                             block, sort_order))
        logger.info(f"Output spec added: {output_id}")
    
    def get_output_specs(self, schema: str = None, block: str = None,
                        is_active: bool = True) -> List[Dict]:
        """
        查询输出定义
        
        Args:
            schema: Schema类型（可选）
            block: 区块（可选）
            is_active: 是否激活（可选）
            
        Returns:
            输出定义列表
        """
        sql = "SELECT * FROM meta.output_spec WHERE 1=1"
        params = []
        
        if schema:
            sql += " AND schema = ?"
            params.append(schema)
        
        if block:
            sql += " AND block = ?"
            params.append(block)
        
        if is_active is not None:
            sql += " AND is_active = ?"
            params.append(is_active)
        
        sql += " ORDER BY block, sort_order NULLS LAST, output_id"
        
        df = self.db.query_df(sql, tuple(params) if params else None)
        return df.to_dict('records')
    
    # ========================================
    # Output Assembly
    # ========================================
    
    def add_output_assembly(self, output_id: str, component_type: str,
                           component_order: int, select_condition: str = None,
                           layout_template: str = None, formatting_rules: Dict = None):
        """
        添加输出组装规则
        
        Args:
            output_id: 输出ID
            component_type: 组件类型
            component_order: 组件顺序
            select_condition: 选择条件
            layout_template: 布局模板
            formatting_rules: 格式化规则
        """
        rules_json = json.dumps(formatting_rules) if formatting_rules else None
        
        sql = """
            INSERT INTO meta.output_assembly
            (output_id, component_type, component_order, select_condition,
             layout_template, formatting_rules)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (output_id, component_order)
            DO UPDATE SET
                component_type = EXCLUDED.component_type,
                select_condition = EXCLUDED.select_condition,
                layout_template = EXCLUDED.layout_template,
                formatting_rules = EXCLUDED.formatting_rules,
                updated_at = NOW()
        """
        
        self.db.execute(sql, (output_id, component_type, component_order,
                             select_condition, layout_template, rules_json))
        logger.info(f"Output assembly added: {output_id} component {component_order}")
    
    def get_output_assembly(self, output_id: str) -> List[Dict]:
        """
        查询输出组装规则
        
        Args:
            output_id: 输出ID
            
        Returns:
            组装规则列表
        """
        sql = """
            SELECT * FROM meta.output_assembly
            WHERE output_id = ?
            ORDER BY component_order
        """
        df = self.db.query_df(sql, (output_id,))
        return df.to_dict('records')
