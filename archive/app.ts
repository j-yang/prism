import * as duckdb from '@duckdb/duckdb-wasm';

interface StudyInfo {
  study_code: string;
  indication?: string;
  created_at?: string;
}

interface Output {
  output_id: string;
  output_type: 'table' | 'figure' | 'listing';
  title: string;
  section?: string;
  display_order?: number;
  schema?: string;
  population?: string;
}

interface GoldRow {
  output_id: string;
  group1_name?: string;
  group1_value?: string;
  variable: string;
  category?: string;
  stat_name: string;
  stat_value?: number;
  stat_display?: string;
  row_order?: number;
}

interface DataLineage {
  target_output_id: string;
  target_group_value: string;
  target_variable: string;
  target_stat_name: string;
  source_table?: string;
  source_subjects?: string;
}

interface TraceData {
  outputId: string;
  group: string;
  variable: string;
  stat: string;
  category: string;
}

class DatabaseService {
  private db: duckdb.AsyncDuckDB | null = null;
  private conn: duckdb.AsyncDuckDBConnection | null = null;

  async init(onProgress: (msg: string) => void): Promise<void> {
    onProgress('Initializing DuckDB...');

    const JSDELIVR_BUNDLES = duckdb.getJsDelivrBundles();
    const bundle = await duckdb.selectBundle(JSDELIVR_BUNDLES);

    onProgress('Creating worker...');
    const workerUrl = URL.createObjectURL(
      new Blob([`importScripts("${bundle.mainWorker}");`], { type: 'text/javascript' })
    );
    const worker = new Worker(workerUrl);

    const logger = new duckdb.ConsoleLogger();
    this.db = new duckdb.AsyncDuckDB(logger, worker);

    onProgress('Instantiating WASM...');
    await this.db.instantiate(bundle.mainModule, bundle.pthreadWorker);
    URL.revokeObjectURL(workerUrl);

    onProgress('Connecting...');
    this.conn = await this.db.connect();

    onProgress('Loading study database...');
    const response = await fetch('study.duckdb');
    if (!response.ok) {
      throw new Error(`Failed to load study.duckdb: ${response.status}`);
    }
    const buffer = await response.arrayBuffer();
    await this.db.registerFileBuffer('study.duckdb', new Uint8Array(buffer));
    await this.conn.query(`ATTACH 'study.duckdb' AS study (READ_ONLY)`);

    onProgress('Ready!');
  }

  async query<T = Record<string, unknown>>(sql: string): Promise<T[]> {
    if (!this.conn) throw new Error('Database not connected');
    const result = await this.conn.query(sql);
    return result.toArray().map(row => row.toJSON() as T);
  }
}

class PortalApp {
  private db: DatabaseService;
  private studyMeta: StudyInfo | null = null;

  constructor() {
    this.db = new DatabaseService();
  }

  private log(msg: string): void {
    console.log('[PRISM]', msg);
    const statusEl = document.getElementById('main-content');
    if (statusEl) {
      statusEl.innerHTML = `<div class="loading">${msg}</div>`;
    }
  }

  async init(): Promise<void> {
    try {
      await this.db.init(msg => this.log(msg));
      await this.loadStudyMeta();
      await this.renderNavigation();
      await this.showWelcome();
      this.bindGlobalEvents();
    } catch (error) {
      console.error('[PRISM ERROR]', error);
      document.getElementById('main-content')!.innerHTML = 
        `<div style="padding:20px;color:#c00;">
          <h3>Failed to initialize</h3>
          <p style="font-family:monospace;">${(error as Error).message}</p>
          <pre style="font-size:11px;color:#666;margin-top:10px;white-space:pre-wrap;max-height:200px;overflow:auto;">${(error as Error).stack}</pre>
        </div>`;
    }
  }

  private async loadStudyMeta(): Promise<void> {
    try {
      const studyInfo = await this.db.query<StudyInfo>("SELECT * FROM study.meta.study_info LIMIT 1");
      this.studyMeta = studyInfo[0] || { study_code: 'Unknown' };

      document.getElementById('study-code')!.textContent = this.studyMeta.study_code || 'Study';
      document.getElementById('generated-date')!.textContent = 
        `Generated: ${new Date().toLocaleDateString()}`;
      document.getElementById('footer-date')!.textContent = new Date().toLocaleDateString();
    } catch (e) {
      console.warn('Could not load study metadata:', e);
      this.studyMeta = { study_code: 'Study' };
    }
  }

  private async renderNavigation(): Promise<void> {
    try {
      const outputs = await this.db.query<Output>(`
        SELECT output_id, output_type, title, section
        FROM study.meta.outputs
        ORDER BY section NULLS LAST, display_order NULLS LAST
      `);

      const tables = outputs.filter(o => o.output_type === 'table');
      const figures = outputs.filter(o => o.output_type === 'figure');
      const listings = outputs.filter(o => o.output_type === 'listing');

      document.getElementById('nav-tables')!.innerHTML = tables
        .map(o => `<li><a href="#" data-output="${o.output_id}">${o.output_id}</a></li>`)
        .join('') || '<li style="color:#999;padding:6px 15px;">No tables</li>';

      document.getElementById('nav-figures')!.innerHTML = figures.length > 0
        ? figures.map(o => `<li><a href="#" data-output="${o.output_id}">${o.output_id}</a></li>`).join('')
        : '<li style="color:#999;padding:6px 15px;font-size:12px;">No figures</li>';

      document.getElementById('nav-listings')!.innerHTML = listings.length > 0
        ? listings.map(o => `<li><a href="#" data-output="${o.output_id}">${o.output_id}</a></li>`).join('')
        : '<li style="color:#999;padding:6px 15px;font-size:12px;">No listings</li>';

      document.querySelectorAll('#navigation a[data-output]').forEach(a => {
        a.addEventListener('click', (e) => {
          e.preventDefault();
          this.showOutput((a as HTMLElement).dataset.output!);
        });
      });
    } catch (e) {
      console.error('Failed to load outputs:', e);
    }
  }

  private async showWelcome(): Promise<void> {
    const content = document.getElementById('main-content')!;
    content.innerHTML = `
      <h2 style="margin-bottom:20px;">Study ${this.studyMeta?.study_code || 'Overview'}</h2>
      <p style="color:#666;margin-bottom:30px;">
        Click on a table from the navigation to view results.
        Click on any <span style="color:#06c;text-decoration:underline;">number</span> to see traceability.
      </p>
      <h3 style="margin-bottom:15px;">Available Outputs</h3>
      <div id="welcome-outputs">Loading...</div>
    `;

    try {
      const outputs = await this.db.query<Output>(`
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

      document.getElementById('welcome-outputs')!.innerHTML = html || 'No outputs defined';
    } catch (e) {
      document.getElementById('welcome-outputs')!.innerHTML = 'Error loading outputs';
    }
  }

  async showOutput(outputId: string): Promise<void> {
    const content = document.getElementById('main-content')!;
    content.innerHTML = '<div class="loading">Loading...</div>';

    try {
      const outputs = await this.db.query<Output>(
        `SELECT * FROM study.meta.outputs WHERE output_id = '${outputId}'`
      );

      if (outputs.length === 0) {
        content.innerHTML = `<p>Output ${outputId} not found</p>`;
        return;
      }

      const output = outputs[0];
      const schema = output.schema || 'baseline';
      const title = output.title || outputId;

      const goldData = await this.db.query<GoldRow>(`
        SELECT * FROM study.gold.${schema} 
        WHERE output_id = '${outputId}'
        ORDER BY row_order NULLS LAST, group1_value, variable, category NULLS FIRST
      `);

      if (goldData.length === 0) {
        content.innerHTML = `<div class="output-title">${title}</div><p>No data available.</p>`;
        return;
      }

      content.innerHTML = this.renderOutputTable(outputId, title, goldData, output);
    } catch (e) {
      content.innerHTML = `<p>Error: ${(e as Error).message}</p>`;
    }
  }

  private renderOutputTable(
    outputId: string,
    title: string,
    data: GoldRow[],
    outputMeta: Output
  ): string {
    const groups = [...new Set(data.map(d => d.group1_value).filter((v): v is string => Boolean(v)))].sort();
    const variables = [...new Set(data.map(d => d.variable).filter((v): v is string => Boolean(v)))];

    interface RowData {
      variable: string;
      category: string | null;
      stat: string;
      cells: Record<string, GoldRow | undefined>;
    }

    const rows: RowData[] = [];
    for (const variable of variables) {
      const varData = data.filter(d => d.variable === variable);
      const categories = [...new Set(varData.map(d => d.category).filter((v): v is string => Boolean(v)))];

      if (categories.length === 0) {
        for (const stat of ['n', 'mean', 'sd', 'median', 'min', 'max']) {
          const row: RowData = { variable, category: null, stat, cells: {} };
          for (const group of groups) {
            row.cells[group] = varData.find(d => d.group1_value === group && d.stat_name === stat);
          }
          rows.push(row);
        }
      } else {
        for (const category of categories) {
          const catData = varData.filter(d => d.category === category);
          for (const stat of ['n', 'pct']) {
            const row: RowData = { variable, category, stat, cells: {} };
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

    let currentVar: string | null = null;
    for (const row of rows) {
      if (row.variable !== currentVar) {
        html += `<tr><td colspan="${groups.length + 1}" style="font-weight:bold;padding-top:15px;">${row.variable}</td></tr>`;
        currentVar = row.variable;
      }

      const label = row.category
        ? row.category
        : row.stat.charAt(0).toUpperCase() + row.stat.slice(1);
      html += `<tr><td class="indent-1">${label}${row.stat === 'pct' ? ' (%)' : ''}</td>`;

      for (const group of groups) {
        const cell = row.cells[group];
        const clickable = (row.stat === 'n' || row.stat === 'pct') ? 'clickable' : '';
        const traceData: TraceData = {
          outputId,
          group,
          variable: row.variable,
          stat: row.stat,
          category: row.category || ''
        };
        html += `<td class="numeric ${clickable}" data-trace='${JSON.stringify(traceData)}'>${
          cell ? (cell.stat_display || cell.stat_value || '-') : '-'
        }</td>`;
      }
      html += '</tr>';
    }

    html += `</tbody></table>
      <div class="output-footnote">Population: ${outputMeta.population || 'All'} | Click highlighted numbers for traceability</div>`;

    setTimeout(() => this.bindTableClickEvents(), 0);
    return html;
  }

  private bindTableClickEvents(): void {
    document.querySelectorAll('td.clickable').forEach(td => {
      td.addEventListener('click', () => {
        const data = JSON.parse((td as HTMLElement).dataset.trace!) as TraceData;
        this.showTraceability(data.outputId, data.group, data.variable, data.stat, data.category);
      });
    });
  }

  private async showTraceability(
    outputId: string,
    group: string,
    variable: string,
    statName: string,
    category: string
  ): Promise<void> {
    const modal = document.getElementById('modal-overlay')!;
    const body = document.getElementById('modal-body')!;

    body.innerHTML = '<div class="loading">Loading...</div>';
    modal.classList.add('active');

    try {
      const lineage = await this.db.query<DataLineage>(`
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
      const subjects: string[] = lin.source_subjects ? JSON.parse(lin.source_subjects) : [];

      interface RawValue {
        usubjid: string;
        [key: string]: unknown;
      }

      let rawData: RawValue[] = [];
      if (subjects.length > 0 && lin.source_table) {
        try {
          const subjectList = subjects.map(s => `'${s}'`).join(',');
          rawData = await this.db.query<RawValue>(
            `SELECT usubjid, ${variable.toLowerCase()} FROM study.silver.baseline WHERE usubjid IN (${subjectList})`
          );
        } catch {}
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
        const varKey = variable.toLowerCase();
        html += `<div class="modal-section">
          <h4>Raw Values</h4>
          <table><thead><tr><th>Subject</th><th>Value</th></tr></thead>
          <tbody>${rawData.map(r => 
            `<tr><td>${r.usubjid}</td><td>${(r[varKey] as string) || '-'}</td></tr>`
          ).join('')}</tbody></table>
        </div>`;
      }

      body.innerHTML = html;
    } catch (e) {
      body.innerHTML = `<p>Error: ${(e as Error).message}</p>`;
    }
  }

  async showDataBrowser(): Promise<void> {
    const content = document.getElementById('main-content')!;
    content.innerHTML = `<div class="data-browser">
      <h2>Data Browser</h2>
      <div id="data-table">Loading...</div>
    </div>`;

    try {
      const data = await this.db.query('SELECT * FROM study.silver.baseline LIMIT 100');
      if (data.length === 0) {
        document.getElementById('data-table')!.innerHTML = '<p>No data.</p>';
        return;
      }

      const columns = Object.keys(data[0]);
      const html = `<table class="output-table"><thead><tr>${columns.map(c => `<th>${c}</th>`).join('')}</tr></thead>
        <tbody>${data.map(row => 
          `<tr>${columns.map(c => `<td>${row[c] ?? ''}</td>`).join('')}</tr>`
        ).join('')}</tbody></table>
        <p style="font-size:11px;color:#999;margin-top:10px;">${data.length} rows</p>`;

      document.getElementById('data-table')!.innerHTML = html;
    } catch (e) {
      document.getElementById('data-table')!.innerHTML = `<p>Error: ${(e as Error).message}</p>`;
    }
  }

  private closeModal(): void {
    document.getElementById('modal-overlay')!.classList.remove('active');
  }

  private bindGlobalEvents(): void {
    document.getElementById('modal-close')!.addEventListener('click', () => this.closeModal());
    document.getElementById('modal-overlay')!.addEventListener('click', (e) => {
      if (e.target === e.currentTarget) this.closeModal();
    });
    document.getElementById('nav-browser')!.addEventListener('click', (e) => {
      e.preventDefault();
      this.showDataBrowser();
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const app = new PortalApp();
  app.init();
});
