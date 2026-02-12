# Phase 1 Gap Analysis - Bronze Layer Readiness

**Date**: 2026-02-12  
**Question**: 导入SAS7BDAT格式的raw data，完成Bronze layer所有准备都完成了吗？

## ✅ 已完成的准备工作

### 1. 数据库基础设施 ✅
- [x] DuckDB连接管理 (`database.py`)
- [x] Schema管理功能
- [x] 查询接口 (query_df, query_one, query_all)
- [x] 事务支持

### 2. Metadata体系 ✅
- [x] 5个元数据表设计完成
- [x] CRUD接口实现 (`metadata.py`)
- [x] schema_docs: 表结构文档
- [x] data_catalog: 变量注册表
- [x] derivations: 转换规则
- [x] output_spec & output_assembly

### 3. Bronze Schema生成 ✅
- [x] ALS解析器 (`parse_als_v2.py`)
- [x] Form分类器 (baseline/longitudinal/occurrence)
- [x] 自动生成Bronze DDL
- [x] 自动填充metadata
- [x] 处理重复列名
- [x] 处理缺失variable_oid

### 4. 测试验证 ✅
- [x] 测试脚本 (test_phase1.py, test_phase1_3.py)
- [x] 真实ALS文件测试通过 (103 forms, 1279 fields)

---

## ❌ 缺失的关键功能

### 1. **SAS7BDAT文件读取** ❌ CRITICAL
**当前状态**: requirements.txt中没有SAS读取库

**需要添加**:
```python
# 方案A: pandas内置（性能较差，功能有限）
pandas>=2.0.0  # 已有

# 方案B: pyreadstat（推荐，快速，功能完整）
pyreadstat>=1.2.0  # ❌ 未安装

# 方案C: sas7bdat（纯Python，较慢）
sas7bdat>=2.2.3  # ❌ 未安装
```

**推荐**: `pyreadstat` - C底层，速度快，支持value labels，元数据完整

---

### 2. **数据导入核心模块** ❌ CRITICAL
**缺失文件**: `src/prismdb/init_bronze.py`

**需要实现的功能**:
```python
class BronzeLoader:
    def load_sas_file(sas_path, form_oid, db) -> int:
        """加载单个SAS文件到Bronze表"""
        # 1. 读取SAS文件
        # 2. 验证列是否匹配Bronze schema
        # 3. 数据类型转换
        # 4. 插入DuckDB
        pass
    
    def load_study_data(study_path, db) -> Dict:
        """批量加载研究所有数据"""
        # 遍历所有SAS文件，映射到forms
        pass
    
    def validate_data(df, form_oid, db) -> List[str]:
        """数据质量检查"""
        # 检查必填列
        # 检查数据类型
        # 检查取值范围
        pass
```

---

### 3. **数据类型映射** ❌ CRITICAL
**问题**: SAS数据类型 → DuckDB数据类型转换

**需要处理的情况**:
| SAS类型 | DuckDB类型 | 注意事项 |
|---------|------------|----------|
| CHAR/VARCHAR | TEXT | ✅ 简单 |
| NUM (整数) | INTEGER | ⚠️ 需判断精度 |
| NUM (小数) | DOUBLE | ⚠️ 精度损失 |
| DATE | DATE | ⚠️ SAS日期基准1960-01-01 |
| DATETIME | TIMESTAMP | ⚠️ 需转换 |
| TIME | TIME | ⚠️ 需转换 |

**当前状态**: `_map_data_format()` 只映射了ALS类型，没有SAS类型映射

---

### 4. **数据验证规则** ❌ IMPORTANT
**需要实现**:
- [ ] 必填字段检查 (usubjid, record_date等)
- [ ] 数据类型校验
- [ ] 取值范围检查 (codelist validation)
- [ ] 日期逻辑校验 (开始日期 <= 结束日期)
- [ ] 跨表一致性检查 (usubjid存在于DM)
- [ ] 重复记录检测

**建议**: 在metadata中增加validation_rules表

---

### 5. **USUBJID标准化** ❌ IMPORTANT
**问题**: 不同SAS数据集可能使用不同的ID列名
- USUBJID (标准)
- SUBJID (某些研究)
- PTID (Patient ID)
- StudyID || Site || Subject (组合键)

**需要**: 
- ID列自动检测
- ID格式标准化
- Site/Subject分离逻辑

---

### 6. **日期时间处理** ❌ IMPORTANT
**SAS日期特殊性**:
- SAS日期基准: 1960-01-01
- Python/DuckDB: 1970-01-01
- 需要转换: `sas_date + timedelta(days=3653)`

**需要处理**:
```python
def convert_sas_date(sas_value):
    """SAS日期 → Python datetime"""
    from datetime import datetime, timedelta
    if pd.isna(sas_value):
        return None
    sas_epoch = datetime(1960, 1, 1)
    return sas_epoch + timedelta(days=int(sas_value))
```

---

### 7. **缺失值处理** ❌ IMPORTANT
**SAS缺失值表示**:
- `.` (数值缺失)
- `''` (字符缺失)
- `.A` - `.Z`, `._` (特殊缺失值)

**DuckDB**:
- `NULL` (统一表示)

**需要**: 映射规则 + 元数据记录

---

### 8. **数据质量报告** ❌ NICE TO HAVE
**建议功能**:
```python
def generate_quality_report(db, study_code) -> Dict:
    """生成数据质量报告"""
    return {
        'record_counts': {...},        # 各表记录数
        'missing_rates': {...},        # 缺失率
        'duplicate_checks': {...},     # 重复检测
        'date_range_checks': {...},    # 日期范围
        'codelist_violations': {...}   # 编码违规
    }
```

---

### 9. **增量导入支持** ❌ NICE TO HAVE
**场景**: 数据锁定前的多次导入

**需要**:
- UPSERT逻辑 (INSERT OR REPLACE)
- 变更追踪 (audit_log)
- 数据版本管理

---

### 10. **性能优化** ❌ NICE TO HAVE
**大数据集考虑** (>1M records):
- 批量插入 (batch insert)
- 索引策略
- 分区表 (按study_code?)
- 并行加载

---

## 📋 优先级排序

### P0 - 必须立即实现 (阻塞Phase 1.4)
1. ✅ ~~安装pyreadstat~~ → 添加到requirements.txt
2. ✅ 实现`init_bronze.py`核心模块
3. ✅ SAS日期时间转换
4. ✅ 基本数据验证（必填字段）

### P1 - 重要但可延后
5. 数据类型智能映射
6. USUBJID标准化
7. Codelist验证
8. 数据质量报告

### P2 - 增强功能
9. 增量导入
10. 性能优化（并行、批量）

---

## 🎯 Phase 1.4 最小可行实现 (MVP)

### 必须实现的功能
```python
# src/prismdb/init_bronze.py

def load_sas_to_bronze(
    sas_path: str,          # SAS文件路径
    form_oid: str,          # 对应的form OID
    db: Database,           # 数据库连接
    validate: bool = True   # 是否验证
) -> Dict[str, Any]:
    """
    MVP功能:
    1. 读取SAS文件 (pyreadstat)
    2. 检查必填列 (usubjid)
    3. 转换SAS日期
    4. 插入Bronze表
    5. 返回统计信息
    """
    pass
```

### 测试目标
- [ ] 成功导入1个SAS文件 (如DM.sas7bdat)
- [ ] 数据在DuckDB中可查询
- [ ] 日期正确转换
- [ ] 记录数匹配

---

## 🚀 建议实施路径

### Step 1: 环境准备 (5分钟)
```bash
pip install pyreadstat
```

### Step 2: 创建init_bronze.py (30分钟)
- 实现基础的SAS文件读取
- 实现日期转换
- 实现数据插入

### Step 3: 创建测试 (15分钟)
```python
# tests/test_phase1_4.py
def test_load_sas_file():
    # 准备测试SAS文件
    # 加载到Bronze
    # 验证数据
```

### Step 4: 真实数据测试 (如果有的话)
- 导入DM.sas7bdat
- 导入AE.sas7bdat
- 检查数据完整性

---

## 总结

### ✅ 准备充分的部分 (80%)
- 数据库基础设施完整
- Metadata体系完善
- Bronze schema自动生成
- 测试框架完备

### ❌ 关键缺失 (20%)
- **SAS文件读取能力** (CRITICAL)
- **数据导入实现** (CRITICAL)
- **日期时间转换** (CRITICAL)
- 数据验证规则 (IMPORTANT)

### 🎯 结论

**回答用户问题**: **No, 还差关键的最后一公里**

虽然基础设施已经搭建完善（数据库、metadata、schema生成），但**实际从SAS文件读取数据并写入Bronze的核心代码还未实现**。

**需要补充**:
1. 安装pyreadstat
2. 实现init_bronze.py (约50行核心代码)
3. SAS日期转换函数 (约10行)
4. 基本验证逻辑 (约20行)

**预计工作量**: 1-2小时即可完成MVP，达到可导入真实数据的程度。

---

**下一步行动**:
1. 是否现在开始实现init_bronze.py？
2. 是否有示例SAS文件用于测试？
3. 是否需要先实现完整验证规则？还是MVP先行？
