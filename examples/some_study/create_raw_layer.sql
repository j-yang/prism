-- ============================================
-- Metadata Tables
-- ============================================

CREATE TABLE IF NOT EXISTS studies (
    study_code TEXT PRIMARY KEY,
    study_name TEXT,
    indication TEXT,
    phase TEXT,
    status TEXT DEFAULT 'active',
    edc_schema_file TEXT,
    raw_data_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    study_code TEXT,
    var_name TEXT NOT NULL,
    structure TEXT NOT NULL CHECK (structure IN ('static', 'longitudinal', 'occurrence')),
    label TEXT,
    data_type TEXT,
    source_form TEXT,
    source_field TEXT,
    codelist TEXT,
    is_derived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(study_code, var_name, structure),
    FOREIGN KEY (study_code) REFERENCES studies(study_code)
);

-- ============================================
-- Raw Layer: Static (Bronze)
-- ============================================

CREATE TABLE IF NOT EXISTS raw_static (
    usubjid TEXT PRIMARY KEY,
    study_code TEXT,
    sitenum TEXT,
    subjnum REAL,
    subjid TEXT,
    indtyp REAL,
    mh1yn REAL,
    mh1term TEXT,
    mh1stdat TEXT,
    mh1ongo REAL,
    mh1endat TEXT,
    mh1preyn REAL,
    mh1typ REAL,
    mh1typo TEXT,
    mh1dose TEXT,
    mh1dosu REAL,
    mh1dosuo TEXT,
    mh1frq REAL,
    mh1frqo TEXT,
    mh1route REAL,
    mh1routo TEXT,
    mh2yn REAL,
    mh2term TEXT,
    mh2typ REAL,
    mh2stdat TEXT,
    mh2ongo REAL,
    mh2endat TEXT,
    cp1perf REAL,
    cp1rsnd TEXT,
    cp1dat TEXT,
    cp1com TEXT,
    cp17perf REAL,
    cp17rsnd TEXT,
    cp17dat TEXT,
    cp17com TEXT,
    cp2perf REAL,
    cp2rsnd TEXT,
    cp2dat TEXT,
    cp2com TEXT,
    cp3perf REAL,
    cp3rsnd TEXT,
    cp3dat TEXT,
    cp3com TEXT,
    cp4perf REAL,
    cp4rsnd TEXT,
    cp4dat TEXT,
    cp4com TEXT,
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Raw Layer: Longitudinal (Bronze)
-- ============================================

CREATE TABLE IF NOT EXISTS raw_longitudinal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usubjid TEXT NOT NULL,
    study_code TEXT,
    domain TEXT,
    paramcd TEXT NOT NULL,
    param TEXT,
    visit TEXT,
    visitnum INTEGER,
    adt TEXT,
    aval REAL,
    avalc TEXT,
    ablfl TEXT,
    source_form TEXT,
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(usubjid, domain, paramcd, visit)
);

-- ============================================
-- Raw Layer: Occurrence (Bronze)
-- ============================================

CREATE TABLE IF NOT EXISTS raw_occurrence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usubjid TEXT NOT NULL,
    study_code TEXT,
    domain TEXT NOT NULL,
    seq INTEGER,
    term TEXT,
    decod TEXT,
    cat TEXT,
    scat TEXT,
    astdt TEXT,
    aendt TEXT,
    source_form TEXT,
    visdat TEXT,
    svstat REAL,
    svrsnd TEXT,
    unshei REAL,
    unswei REAL,
    unscv1 REAL,
    unscv2 REAL,
    unscv4 REAL,
    unscv5 REAL,
    unscv3 REAL,
    unsmk6 REAL,
    unsmk7 REAL,
    unseg1 REAL,
    unsecho REAL,
    unssr REAL,
    unseg2 REAL,
    unsvs1 REAL,
    unspe REAL,
    unsre REAL,
    unslb8 REAL,
    unslb9 REAL,
    unslb13 REAL,
    unslb14 REAL,
    unslb19 REAL,
    unslb16 REAL,
    unslb17 REAL,
    unslb18 REAL,
    unslb10 REAL,
    unslb11 REAL,
    unslb12 REAL,
    unslb1 REAL,
    unslb2 REAL,
    unslb3 REAL,
    unslb15 REAL,
    unslb4 REAL,
    unslb5 REAL,
    unslb6 REAL,
    unscp10 REAL,
    unslb7 REAL,
    unscp11 REAL,
    unsgf1 REAL,
    unsgf2 REAL,
    unscp16 REAL,
    unscp5 REAL,
    unscp6 REAL,
    unscp7 REAL,
    unscp8 REAL,
    unscp9 REAL,
    unscp12 REAL,
    unscp13 REAL,
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(usubjid, domain, seq)
);

-- ============================================
-- Indexes
-- ============================================

CREATE INDEX IF NOT EXISTS idx_raw_static_study ON raw_static(study_code);
CREATE INDEX IF NOT EXISTS idx_raw_long_usubjid ON raw_longitudinal(usubjid);
CREATE INDEX IF NOT EXISTS idx_raw_long_paramcd ON raw_longitudinal(paramcd);
CREATE INDEX IF NOT EXISTS idx_raw_long_visit ON raw_longitudinal(visit);
CREATE INDEX IF NOT EXISTS idx_raw_long_domain ON raw_longitudinal(domain);
CREATE INDEX IF NOT EXISTS idx_raw_occur_usubjid ON raw_occurrence(usubjid);
CREATE INDEX IF NOT EXISTS idx_raw_occur_domain ON raw_occurrence(domain);