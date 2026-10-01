var PHASES = Object.freeze({
  eq: Object.freeze({
    current: "eq_current",
    history: "eq_history",
    meta: "eq_meta"
  }),
  qual: Object.freeze({
    current: "qual_current",
    history: "qual_history",
    meta: "qual_meta"
  })
});

var LEGACY_EQ = Object.freeze({
  current: "current",
  history: "history",
  meta: "meta"
});

var CURRENT_HEADERS = Object.freeze([
  "ID",
  "data_entrada_fase",
  "aging_dias",
  "status_saude",
  "grupo_fila",
  "prioridade_operacional",
  "ordem_prioridade"
]);

var HISTORY_HEADERS = Object.freeze([
  "data",
  "atualizado_em",
  "estoque",
  "prioridade_hoje",
  "backlog",
  "dentro_sla",
  "atencao",
  "limiar",
  "fora_sla_7d",
  "criticos",
  "fora_sla_total",
  "pct_fora_sla_total",
  "aging_medio",
  "aging_mediano",
  "aging_max"
]);

var TIME_ZONE = "America/Sao_Paulo";


function doGet() {
  return jsonResponse_({
    ok: true,
    service: "central-funil-marketing",
    version: "1.5"
  });
}


function doPost(event) {
  try {
    var request = parseRequest_(event);
    authorize_(request.secret);

    if (request.action === "health") {
      return jsonResponse_({ ok: true, service: "central-funil-marketing" });
    }

    var phase = validatePhase_(request.phase);
    var result = withScriptLock_(function () {
      var spreadsheet = getSpreadsheet_();
      var sheets = ensurePhaseSheets_(spreadsheet, phase);

      if (request.action === "load") {
        return loadPhase_(sheets);
      }
      if (request.action === "save") {
        return savePhase_(sheets, request);
      }
      throw new Error("Ação inválida. Use 'health', 'load' ou 'save'.");
    });

    return jsonResponse_(result);
  } catch (error) {
    return jsonResponse_({
      ok: false,
      error: error && error.message ? error.message : String(error)
    });
  }
}


function parseRequest_(event) {
  if (!event || !event.postData || !event.postData.contents) {
    throw new Error("Corpo JSON ausente.");
  }

  var request;
  try {
    request = JSON.parse(event.postData.contents);
  } catch (error) {
    throw new Error("Corpo JSON inválido.");
  }

  if (!request || typeof request !== "object") {
    throw new Error("Corpo JSON inválido.");
  }
  return request;
}


function authorize_(providedSecret) {
  var expectedSecret = PropertiesService.getScriptProperties()
    .getProperty("CENTRAL_API_SECRET");

  if (!expectedSecret) {
    throw new Error("CENTRAL_API_SECRET não configurado nas propriedades do script.");
  }
  if (!providedSecret || String(providedSecret) !== String(expectedSecret)) {
    throw new Error("Não autorizado.");
  }
}


function validatePhase_(phase) {
  var key = String(phase || "").trim().toLowerCase();
  if (!Object.prototype.hasOwnProperty.call(PHASES, key)) {
    throw new Error("Fase inválida. Use 'eq' ou 'qual'.");
  }
  return key;
}


function getSpreadsheet_() {
  var spreadsheetId = PropertiesService.getScriptProperties()
    .getProperty("SPREADSHEET_ID");
  if (!spreadsheetId) {
    throw new Error("SPREADSHEET_ID não configurado nas propriedades do script.");
  }
  return SpreadsheetApp.openById(spreadsheetId);
}


function withScriptLock_(callback) {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(30000)) {
    throw new Error("Não foi possível obter o lock de atualização. Tente novamente.");
  }

  try {
    return callback();
  } finally {
    lock.releaseLock();
  }
}


function ensurePhaseSheets_(spreadsheet, phase) {
  if (phase === "eq") {
    migrateLegacyEq_(spreadsheet);
  }

  var config = PHASES[phase];
  return {
    current: getOrCreateSheet_(spreadsheet, config.current),
    history: getOrCreateSheet_(spreadsheet, config.history),
    meta: getOrCreateSheet_(spreadsheet, config.meta)
  };
}


function migrateLegacyEq_(spreadsheet) {
  ["current", "history", "meta"].forEach(function (kind) {
    var targetName = PHASES.eq[kind];
    var legacyName = LEGACY_EQ[kind];
    var target = spreadsheet.getSheetByName(targetName);
    var legacy = spreadsheet.getSheetByName(legacyName);

    if (!target && legacy) {
      legacy.setName(targetName);
      return;
    }

    if (!target) {
      spreadsheet.insertSheet(targetName);
      return;
    }

    if (legacy && target.getLastRow() === 0 && legacy.getLastRow() > 0) {
      copySheetValues_(legacy, target);
    }
  });
}


function getOrCreateSheet_(spreadsheet, name) {
  return spreadsheet.getSheetByName(name) || spreadsheet.insertSheet(name);
}


function copySheetValues_(source, target) {
  var values = source.getDataRange().getValues();
  target.clearContents();
  if (values.length && values[0].length) {
    target.getRange(1, 1, values.length, values[0].length).setValues(values);
  }
}


function loadPhase_(sheets) {
  return {
    ok: true,
    current: readTable_(sheets.current),
    history: readTable_(sheets.history),
    meta: readMeta_(sheets.meta)
  };
}


function savePhase_(sheets, request) {
  if (!Array.isArray(request.current)) {
    throw new Error("Campo 'current' deve ser uma lista.");
  }
  if (!request.history_row || typeof request.history_row !== "object") {
    throw new Error("Campo 'history_row' é obrigatório.");
  }
  if (!request.meta || typeof request.meta !== "object") {
    throw new Error("Campo 'meta' é obrigatório.");
  }

  writeTable_(sheets.current, request.current, CURRENT_HEADERS);
  upsertDailyHistory_(sheets.history, request.history_row);
  writeMeta_(sheets.meta, request.meta);
  SpreadsheetApp.flush();

  return { ok: true };
}


function readTable_(sheet) {
  var values = sheet.getDataRange().getValues();
  if (!values.length || !values[0].length || isBlankRow_(values[0])) {
    return [];
  }

  var headers = values[0].map(function (value) { return String(value).trim(); });
  return values.slice(1)
    .filter(function (row) { return !isBlankRow_(row); })
    .map(function (row) {
      var record = {};
      headers.forEach(function (header, index) {
        if (header) {
          record[header] = jsonValue_(row[index]);
        }
      });
      return record;
    });
}


function writeTable_(sheet, records, headers) {
  sheet.clearContents();
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);

  if (!records.length) {
    return;
  }

  var values = records.map(function (record) {
    return headers.map(function (header) {
      var value = record[header];
      return value === null || typeof value === "undefined" ? "" : value;
    });
  });
  sheet.getRange(2, 1, values.length, headers.length).setValues(values);
}


function upsertDailyHistory_(sheet, historyRow) {
  var incomingDate = dateKey_(historyRow.data);
  if (!incomingDate) {
    throw new Error("history_row.data é obrigatório.");
  }

  var history = readTable_(sheet);
  var replaced = false;
  history = history.map(function (row) {
    if (dateKey_(row.data) === incomingDate) {
      replaced = true;
      return historyRow;
    }
    return row;
  });

  if (!replaced) {
    history.push(historyRow);
  }

  history.sort(function (left, right) {
    return dateKey_(left.data).localeCompare(dateKey_(right.data));
  });
  writeTable_(sheet, history, HISTORY_HEADERS);
}


function readMeta_(sheet) {
  var values = sheet.getDataRange().getValues();
  if (!values.length || !values[0].length || isBlankRow_(values[0])) {
    return {};
  }

  var firstHeader = String(values[0][0] || "").trim().toLowerCase();
  var secondHeader = String(values[0][1] || "").trim().toLowerCase();
  if (
    ["chave", "key"].indexOf(firstHeader) >= 0 &&
    ["valor", "value"].indexOf(secondHeader) >= 0
  ) {
    var meta = {};
    values.slice(1).forEach(function (row) {
      var key = String(row[0] || "").trim();
      if (key) {
        meta[key] = jsonValue_(row[1]);
      }
    });
    return meta;
  }

  var records = readTable_(sheet);
  return records.length ? records[0] : {};
}


function writeMeta_(sheet, meta) {
  var keys = Object.keys(meta);
  var values = [["chave", "valor"]].concat(keys.map(function (key) {
    var value = meta[key];
    return [key, value === null || typeof value === "undefined" ? "" : value];
  }));

  sheet.clearContents();
  sheet.getRange(1, 1, values.length, 2).setValues(values);
}


function dateKey_(value) {
  if (Object.prototype.toString.call(value) === "[object Date]" && !isNaN(value)) {
    return Utilities.formatDate(value, TIME_ZONE, "yyyy-MM-dd");
  }
  var text = String(value || "").trim();
  var match = text.match(/^(\d{4}-\d{2}-\d{2})/);
  return match ? match[1] : "";
}


function jsonValue_(value) {
  if (Object.prototype.toString.call(value) === "[object Date]" && !isNaN(value)) {
    return value.toISOString();
  }
  return value;
}


function isBlankRow_(row) {
  return row.every(function (value) {
    return value === "" || value === null || typeof value === "undefined";
  });
}


function jsonResponse_(payload) {
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}
