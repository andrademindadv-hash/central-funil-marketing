const assert = require("assert");
const fs = require("fs");
const vm = require("vm");


class FakeSheet {
  constructor(name, spreadsheet, values = []) {
    this.name = name;
    this.spreadsheet = spreadsheet;
    this.values = values.map((row) => row.slice());
  }

  getName() {
    return this.name;
  }

  setName(name) {
    delete this.spreadsheet.sheets[this.name];
    this.name = name;
    this.spreadsheet.sheets[name] = this;
    return this;
  }

  getLastRow() {
    for (let index = this.values.length - 1; index >= 0; index -= 1) {
      if (this.values[index].some((value) => value !== "" && value != null)) {
        return index + 1;
      }
    }
    return 0;
  }

  getDataRange() {
    return {
      getValues: () => (
        this.values.length ? this.values.map((row) => row.slice()) : [[""]]
      ),
    };
  }

  clearContents() {
    this.values = [];
    return this;
  }

  getRange(row, column, rowCount, columnCount) {
    return {
      setValues: (incoming) => {
        for (let rowOffset = 0; rowOffset < rowCount; rowOffset += 1) {
          const targetRow = row - 1 + rowOffset;
          while (this.values.length <= targetRow) this.values.push([]);
          while (this.values[targetRow].length < column - 1 + columnCount) {
            this.values[targetRow].push("");
          }
          for (let columnOffset = 0; columnOffset < columnCount; columnOffset += 1) {
            this.values[targetRow][column - 1 + columnOffset] =
              incoming[rowOffset][columnOffset];
          }
        }
        return this;
      },
    };
  }
}


class FakeSpreadsheet {
  constructor(initial = {}) {
    this.sheets = {};
    Object.entries(initial).forEach(([name, values]) => {
      this.sheets[name] = new FakeSheet(name, this, values);
    });
  }

  getSheetByName(name) {
    return this.sheets[name] || null;
  }

  insertSheet(name) {
    const sheet = new FakeSheet(name, this);
    this.sheets[name] = sheet;
    return sheet;
  }
}


global.SpreadsheetApp = { flush() {} };
global.Utilities = {
  formatDate(date) {
    return date.toISOString().slice(0, 10);
  },
};

const source = fs.readFileSync("apps-script/Code.gs", "utf8");
vm.runInThisContext(source, { filename: "apps-script/Code.gs" });


function historyRow(date, stock) {
  return {
    data: date,
    atualizado_em: `${date}T12:00:00-03:00`,
    estoque: stock,
    prioridade_hoje: 0,
    backlog: 0,
    dentro_sla: stock,
    atencao: 0,
    limiar: 0,
    fora_sla_7d: 0,
    criticos: 0,
    fora_sla_total: 0,
    pct_fora_sla_total: 0,
    aging_medio: 0,
    aging_mediano: 0,
    aging_max: 0,
  };
}


(function testLegacyMigration() {
  const spreadsheet = new FakeSpreadsheet({
    current: [["ID"], ["LEGACY-1"]],
    history: [["data"], ["2026-09-29"]],
    meta: [["chave", "valor"], ["status", "SUCESSO"]],
  });

  migrateLegacyEq_(spreadsheet);

  assert(spreadsheet.getSheetByName("eq_current"));
  assert(spreadsheet.getSheetByName("eq_history"));
  assert(spreadsheet.getSheetByName("eq_meta"));
  assert.strictEqual(spreadsheet.getSheetByName("current"), null);
})();


(function testSaveLoadAndSameDayReplacement() {
  const spreadsheet = new FakeSpreadsheet();
  const sheets = ensurePhaseSheets_(spreadsheet, "qual");
  const current = [{
    ID: "QUAL-1",
    data_entrada_fase: "2026-09-30 00:00:00",
    aging_dias: 0,
    status_saude: "Dentro do SLA",
    grupo_fila: "Dentro do SLA",
    prioridade_operacional: "Entrada do dia",
    ordem_prioridade: 7,
  }];

  savePhase_(sheets, {
    current,
    history_row: historyRow("2026-09-30", 1),
    meta: { status: "SUCESSO", fase: "QUALIFICADO" },
  });
  savePhase_(sheets, {
    current,
    history_row: historyRow("2026-09-30", 2),
    meta: { status: "SUCESSO", fase: "QUALIFICADO" },
  });

  const loaded = loadPhase_(sheets);
  assert.strictEqual(loaded.ok, true);
  assert.deepStrictEqual(loaded.current, current);
  assert.strictEqual(loaded.history.length, 1);
  assert.strictEqual(loaded.history[0].estoque, 2);
  assert.strictEqual(loaded.meta.fase, "QUALIFICADO");
})();


console.log("Apps Script backend tests OK");
