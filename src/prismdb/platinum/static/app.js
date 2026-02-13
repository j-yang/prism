// PRISM-DB Data Review Portal
// Uses DuckDB WASM for in-browser SQL queries

import * as duckdb from 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@0.10.0/+esm';

let db = null;
let conn = null;
let studyMeta = null;

function log(msg) {
    console.log('[PRISM]', msg);
    const statusEl = document.getElementById('main-content');
    if (statusEl) {
        statusEl.innerHTML = `<div class="loading">${msg}</div>`;
    }
}

async function initDuckDB() {
    log('Loading DuckDB WASM...');
    
    try {
        const MANUAL_BUNDLES = {
            mvp: {
                mainModule: 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@0.10.0/dist/duckdb-mvp.wasm',
                mainWorker: 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@0.10.0/dist/duckdb-browser-mvp.worker.js'
            },
            eh: {
                mainModule: 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@0.10.0/dist/duckdb-eh.wasm',
                mainWorker: 'https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@0.10.0/dist/duckdb-browser-eh.worker.js'
            }
        };
        
        const bundle = await duckdb.selectBundle(MANUAL_BUNDLES);
        const worker = new Worker(bundle.mainWorker);
        const logger = new duckdb.ConsoleLogger();
        db = new duckdb.AsyncDuckDB(logger, worker);
        await db.instantiate(bundle.mainModule);
        
        log('Connecting to database...');
        conn = await db.connect();
        
        log('Loading study database...');
        const response = await fetch('study.duckdb');
        if (!response.ok) {
            throw new Error(`Failed to load study.duckdb: ${response.status}`);
        }
        const buffer = await response.arrayBuffer();
        await db.registerFileBuffer('study.duckdb', new Uint8Array(buffer));
        await conn.query(`ATTACH 'study.duckdb' AS study`);
        
        log('Database loaded!');
        
        await loadStudyMeta();
        await renderNavigation();
        await showWelcome();
        
    } catch (error) {
        console.error('[PRISM ERROR]', error);
        document.getElementById('main-content').innerHTML = 
            `<div style="padding:20px;color:#c00;">
                <h3>Failed to initialize</h3>
                <p style="font-family:monospace;">${error.message}</p>
                <p style="font-size:12px;color:#666;margin-top:10px;">
                    Check browser console for details
                </p>
            </div>`;
    }
}

async function query(sql) {
    const result = await conn.query(sql);
    return result.toArray().map(row => row.toJSON());
}

async function loadStudyMeta() {
    try {
        const studyInfo = await query("SELECT * FROM study.meta.study_info LIMIT 1");
        if (studyInfo.length > 0) {
            studyMeta = studyInfo[0];
        } else {
            studyMeta = { study_code: 'Unknown' };
        }
        
        document.getElementById('study-code').textContent = studyMeta.study_code || 'Study';
        document.getElementById('generated-date').textContent = 
            `Generated: ${new Date().toLocaleDateString()}`;
        document.getElementById('footer-date').textContent = new Date().toLocaleDateString();
        
    } catch (e) {
        console.warn('Could not load study metadata:', e);
        studyMeta = { study_code: 'Study' };
    }
}

async function renderNavigation() {
    try {
        const outputs = await query(`
            SELECT output_id, output_type, title, section
            FROM study.meta.outputs
            ORDER BY section NULLS LAST, display_order NULLS LAST
        `);
        
        const tables = outputs.filter(o => o.output_type === 'table');
        const figures = outputs.filter(o => o.output_type === 'figure');
        const listings = outputs.filter(o => o.output_type === 'listing');
        
        document.getElementById('nav-tables').innerHTML = tables
            .map(o => `<li><a href="#" onclick="showOutput('${o.output_id}')">${o.output_id}</a></li>`)
            .join('') || '<li style="color:#999;padding:6px 15px;">No tables</li>';
        
        document.getElementById('nav-figures').innerHTML = figures.length > 0
            ? figures.map(o => `<li><a href="#" onclick="showOutput('${o.output_id}')">${o.output_id}</a></li>`).join('')
            : '<li style="color:#999;padding:6px 15px;font-size:12px;">No figures</li>';
        
        document.getElementById('nav-listings').innerHTML = listings.length > 0
            ? listings.map(o => `<li><a href="#" onclick="showOutput('${o.output_id}')">${o.output_id}</a></li>`).join('')
            : '<li style="color:#999;padding:6px 15px;font-size:12px;">No listings</li>';
            
    } catch (e) {
        console.error('Failed to load outputs:', e);
    }
}

async function showWelcome() {
    const content = document.getElementById('main-content');
    content.innerHTML = `
        <h2 style="margin-bottom:20px;">Study ${studyMeta.study_code || 'Overview'}</h2>
        <p style="color:#666;margin-bottom:30px;">
            Click on a table from the navigation to view results.
            Click on any <span style="color:#06c;text-decoration:underline;">number</span> to see traceability.
        </p>
        <h3 style="margin-bottom:15px;">Available Outputs</h3>
        <div id="welcome-outputs">Loading...</div>
    `;
    
    try {
        const outputs = await query(`
            SELECT output_id, output_type, title
            FROM study.meta.outputs
            ORDER BY output_type, output_id
        `);
        
        const html = outputs.map(o => `
            <div style="margin-bottom:10px;">
                <strong>${o.output_id}</strong>: ${o.title || 'No title'}
                <span style="color:#999;font-size:11px;">(${o.output_type})</span>
            </div>
        `).join('');
        
        document.getElementById('welcome-outputs').innerHTML = html || 'No outputs defined';
        
    } catch (e) {
        document.getElementById('welcome-outputs').innerHTML = 'Error loading outputs';
    }
}

async function showOutput(outputId) {
    const content = document.getElementById('main-content');
    content.innerHTML = '<div class="loading">Loading...</div>';
    
    try {
        const outputs = await query(`SELECT * FROM study.meta.outputs WHERE output_id = '${outputId}'`);
        
        if (outputs.length === 0) {
            content.innerHTML = `<p>Output ${outputId} not found</p>`;
            return;
        }
        
        const output = outputs[0];
        const schema = output.schema || 'baseline';
        const title = output.title || outputId;
        
        const goldData = await query(`
            SELECT * FROM study.gold.${schema} 
            WHERE output_id = '${outputId}'
            ORDER BY row_order NULLS LAST, group1_value, variable, category NULLS FIRST
        `);
        
        if (goldData.length === 0) {
            content.innerHTML = `<div class="output-title">${title}</div><p>No data available.</p>`;
            return;
        }
        
        const html = renderOutputTable(outputId, title, goldData, output);
        content.innerHTML = html;
        
    } catch (e) {
        content.innerHTML = `<p>Error: ${e.message}</p>`;
    }
}

function renderOutputTable(outputId, title, data, outputMeta) {
    const groups = [...new Set(data.map(d => d.group1_value).filter(v => v))].sort();
    const variables = [...new Set(data.map(d => d.variable).filter(v => v))];
    
    const rows = [];
    for (const variable of variables) {
        const varData = data.filter(d => d.variable === variable);
        const categories = [...new Set(varData.map(d => d.category).filter(c => c))];
        
        if (categories.length === 0) {
            for (const stat of ['n', 'mean', 'sd', 'median', 'min', 'max']) {
                const row = { variable, category: null, stat, cells: {} };
                for (const group of groups) {
                    row.cells[group] = varData.find(d => d.group1_value === group && d.stat_name === stat);
                }
                rows.push(row);
            }
        } else {
            for (const category of categories) {
                const catData = varData.filter(d => d.category === category);
                for (const stat of ['n', 'pct']) {
                    const row = { variable, category, stat, cells: {} };
                    for (const group of groups) {
                        row.cells[group] = catData.find(d => d.group1_value === group && d.stat_name === stat);
                    }
                    rows.push(row);
                }
            }
        }
    }
    
    let html = `<div class="output-title">${title}</div>
        <table class="output-table">
            <thead><tr><th></th>${groups.map(g => `<th class="numeric">${g}</th>`).join('')}</tr></thead>
            <tbody>`;
    
    let currentVar = null;
    for (const row of rows) {
        if (row.variable !== currentVar) {
            html += `<tr><td colspan="${groups.length + 1}" style="font-weight:bold;padding-top:15px;">${row.variable}</td></tr>`;
            currentVar = row.variable;
        }
        
        const label = row.category ? row.category : row.stat.charAt(0).toUpperCase() + row.stat.slice(1);
        html += `<tr><td class="indent-1">${label}${row.stat === 'pct' ? ' (%)' : ''}</td>`;
        
        for (const group of groups) {
            const cell = row.cells[group];
            const clickable = (row.stat === 'n' || row.stat === 'pct') ? 'clickable' : '';
            const onclick = clickable ? `onclick="showTraceability('${outputId}', '${group}', '${row.variable}', '${row.stat}', '${row.category || ''}')"` : '';
            html += `<td class="numeric ${clickable}" ${onclick}>${cell ? (cell.stat_display || cell.stat_value || '-') : '-'}</td>`;
        }
        html += '</tr>';
    }
    
    html += `</tbody></table>
        <div class="output-footnote">Population: ${outputMeta.population || 'All'} | Click highlighted numbers for traceability</div>`;
    
    return html;
}

async function showTraceability(outputId, group, variable, statName, category) {
    const modal = document.getElementById('modal-overlay');
    const body = document.getElementById('modal-body');
    
    body.innerHTML = '<div class="loading">Loading...</div>';
    modal.classList.add('active');
    
    try {
        const lineage = await query(`
            SELECT * FROM study.meta.data_lineage
            WHERE target_output_id = '${outputId}'
              AND target_group_value = '${group}'
              AND target_variable = '${variable}'
              AND target_stat_name = '${statName}'
            LIMIT 1
        `);
        
        if (lineage.length === 0) {
            body.innerHTML = '<p>No traceability data found.</p>';
            return;
        }
        
        const lin = lineage[0];
        const subjects = lin.source_subjects ? JSON.parse(lin.source_subjects) : [];
        
        let rawData = [];
        if (subjects.length > 0 && lin.source_table) {
            try {
                const subjectList = subjects.map(s => `'${s}'`).join(',');
                rawData = await query(`SELECT usubjid, ${variable.toLowerCase()} FROM study.silver.baseline WHERE usubjid IN (${subjectList})`);
            } catch (e) {}
        }
        
        let html = `
            <div class="modal-section">
                <h4>Statistic</h4>
                <p><strong>${group}</strong> | ${variable}${category ? ` | ${category}` : ''} | ${statName}</p>
            </div>
            <div class="modal-section">
                <h4>Subjects (N=${subjects.length})</h4>
                <p class="subject-list">${subjects.join(', ') || 'N/A'}</p>
            </div>
            <div class="modal-section">
                <h4>Source</h4>
                <p>Table: ${lin.source_table || 'N/A'}</p>
            </div>`;
        
        if (rawData.length > 0) {
            html += `<div class="modal-section">
                <h4>Raw Values</h4>
                <table><thead><tr><th>Subject</th><th>Value</th></tr></thead>
                <tbody>${rawData.map(r => `<tr><td>${r.usubjid}</td><td>${r[variable.toLowerCase()] || '-'}</td></tr>`).join('')}</tbody></table>
            </div>`;
        }
        
        body.innerHTML = html;
        
    } catch (e) {
        body.innerHTML = `<p>Error: ${e.message}</p>`;
    }
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('active');
}

async function showDataBrowser() {
    const content = document.getElementById('main-content');
    content.innerHTML = `<div class="data-browser">
        <h2>Data Browser</h2>
        <div id="data-table">Loading...</div>
    </div>`;
    
    try {
        const data = await query('SELECT * FROM study.silver.baseline LIMIT 100');
        if (data.length === 0) {
            document.getElementById('data-table').innerHTML = '<p>No data.</p>';
            return;
        }
        
        const columns = Object.keys(data[0]);
        const html = `<table class="output-table"><thead><tr>${columns.map(c => `<th>${c}</th>`).join('')}</tr></thead>
            <tbody>${data.map(row => `<tr>${columns.map(c => `<td>${row[c] ?? ''}</td>`).join('')}</tr>`).join('')}</tbody></table>
            <p style="font-size:11px;color:#999;margin-top:10px;">${data.length} rows</p>`;
        
        document.getElementById('data-table').innerHTML = html;
    } catch (e) {
        document.getElementById('data-table').innerHTML = `<p>Error: ${e.message}</p>`;
    }
}

document.addEventListener('DOMContentLoaded', initDuckDB);
