(function (root) {
  'use strict';

  var CATEGORIES = {
    length: {
      id: 'length', label: '长度', base: '米', allowNegative: false,
      units: [
        { id: 'mm', name: '毫米', sym: 'mm', factor: 0.001 },
        { id: 'cm', name: '厘米', sym: 'cm', factor: 0.01 },
        { id: 'm',  name: '米',   sym: 'm',  factor: 1 },
        { id: 'km', name: '千米', sym: 'km', factor: 1000 },
        { id: 'in', name: '英寸', sym: 'in', factor: 0.0254 },
        { id: 'ft', name: '英尺', sym: 'ft', factor: 0.3048 },
        { id: 'mi', name: '英里', sym: 'mi', factor: 1609.344 }
      ]
    },
    weight: {
      id: 'weight', label: '重量', base: '千克', allowNegative: false,
      units: [
        { id: 'mg', name: '毫克', sym: 'mg', factor: 0.000001 },
        { id: 'g',  name: '克',   sym: 'g',  factor: 0.001 },
        { id: 'kg', name: '千克', sym: 'kg', factor: 1 },
        { id: 't',  name: '吨',   sym: 't',  factor: 1000 },
        { id: 'oz', name: '盎司', sym: 'oz', factor: 0.028349523125 },
        { id: 'lb', name: '磅',   sym: 'lb', factor: 0.45359237 }
      ]
    },
    temp: {
      id: 'temp', label: '温度', base: '摄氏度', allowNegative: true, special: 'temp',
      units: [
        { id: 'c', name: '摄氏度', sym: '°C' },
        { id: 'f', name: '华氏度', sym: '°F' },
        { id: 'k', name: '开尔文', sym: 'K' }
      ]
    }
  };

  var ABS_ZERO_C = -273.15;

  function toCelsius(fromId, v) {
    if (fromId === 'c') return v;
    if (fromId === 'f') return (v - 32) * 5 / 9;
    if (fromId === 'k') return v - 273.15;
    throw new Error('unknown temperature unit: ' + fromId);
  }

  function fromCelsius(toId, c) {
    if (toId === 'c') return c;
    if (toId === 'f') return c * 9 / 5 + 32;
    if (toId === 'k') return c + 273.15;
    throw new Error('unknown temperature unit: ' + toId);
  }

  function findUnit(cat, uid) {
    var us = CATEGORIES[cat] ? CATEGORIES[cat].units : [];
    for (var i = 0; i < us.length; i++) { if (us[i].id === uid) return us[i]; }
    return null;
  }

  /* 纯换算：入参为已通过校验的数值 */
  function convertRaw(cat, fromId, toId, value) {
    if (cat === 'temp') return fromCelsius(toId, toCelsius(fromId, value));
    var f = findUnit(cat, fromId), t = findUnit(cat, toId);
    if (!f || !t) throw new Error('unknown unit: ' + fromId + ' -> ' + toId);
    return value * f.factor / t.factor;
  }

  var NUM_RE = /^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$/;
  var MAX_INPUT_CHARS = 60;

  function preview(text) {
    return text.length > 12 ? text.slice(0, 12) + '…' : text;
  }

  /* 校验 + 判定：返回 {status, value, level, message}
     status: ok | empty | invalid   level: ok | hint | warn | error */
  function evaluate(cat, fromId, raw) {
    var cfg = CATEGORIES[cat];
    if (!cfg) {
      return { status: 'invalid', value: null, level: 'error', message: '未知的换算类别。' };
    }
    var text = (raw == null ? '' : String(raw)).trim();
    if (text === '') {
      return { status: 'empty', value: null, level: 'hint', message: '请输入数值，结果会自动换算。' };
    }
    if (text.length > MAX_INPUT_CHARS) {
      return { status: 'invalid', value: null, level: 'error',
               message: '输入过长（最多 ' + MAX_INPUT_CHARS + ' 个字符），请输入一个普通数字。' };
    }
    if (!NUM_RE.test(text)) {
      return { status: 'invalid', value: null, level: 'error',
               message: '“' + preview(text) + '”不是有效数字。可输入如 1、-2.5、.5、1e3 的形式。' };
    }
    var v = Number(text);
    if (!isFinite(v)) {
      return { status: 'invalid', value: null, level: 'error', message: '数值超出可计算范围，请换一个较小的数字。' };
    }
    if (!cfg.allowNegative && v < 0) {
      return { status: 'invalid', value: null, level: 'error',
               message: cfg.label + '不能为负值，请输入 0 或正数。' };
    }
    if (cat === 'temp' && toCelsius(fromId, v) < ABS_ZERO_C) {
      return { status: 'ok', value: v, level: 'warn',
               message: '该值低于绝对零度（' + ABS_ZERO_C + ' °C），物理上不存在，此处仅作算术换算。' };
    }
    return { status: 'ok', value: v, level: 'ok', message: '' };
  }

  /* 精度：最多 8 位有效数字，去掉浮点噪声与无意义的长小数 */
  function formatValue(x) {
    if (typeof x !== 'number' || !isFinite(x)) return '—';
    if (x === 0) return '0';
    var abs = Math.abs(x);
    if (abs >= 1e15 || abs < 1e-6) {
      return x.toExponential(5).replace(/\.?0+e/, 'e');
    }
    return String(Number(x.toPrecision(8)));
  }

  root.UnitCore = {
    CATEGORIES: CATEGORIES,
    ABS_ZERO_C: ABS_ZERO_C,
    MAX_INPUT_CHARS: MAX_INPUT_CHARS,
    toCelsius: toCelsius,
    fromCelsius: fromCelsius,
    findUnit: findUnit,
    convertRaw: convertRaw,
    evaluate: evaluate,
    formatValue: formatValue
  };
})(typeof window !== 'undefined' ? window : globalThis);
