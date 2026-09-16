
(function () {
  'use strict';

  /* ---------------- 数据（全部内嵌，无网络请求） ---------------- */
  var DATA = {
    length: {
      label: '长度',
      units: [
        { id: 'mm', name: '毫米', f: 0.001 },
        { id: 'cm', name: '厘米', f: 0.01 },
        { id: 'm',  name: '米',   f: 1 },
        { id: 'km', name: '千米', f: 1000 },
        { id: 'in', name: '英寸', f: 0.0254 },
        { id: 'ft', name: '英尺', f: 0.3048 },
        { id: 'yd', name: '码',   f: 0.9144 },
        { id: 'mi', name: '英里', f: 1609.344 }
      ],
      def: ['m', 'ft'],
      allowNegative: false,
      negMsg: '长度不能为负数，请输入 0 或正数。'
    },
    weight: {
      label: '重量',
      units: [
        { id: 'mg', name: '毫克', f: 0.000001 },
        { id: 'g',  name: '克',   f: 0.001 },
        { id: 'kg', name: '千克', f: 1 },
        { id: 't',  name: '吨',   f: 1000 },
        { id: 'oz', name: '盎司', f: 0.028349523125 },
        { id: 'lb', name: '磅',   f: 0.45359237 }
      ],
      def: ['kg', 'lb'],
      allowNegative: false,
      negMsg: '重量不能为负数，请输入 0 或正数。'
    },
    temperature: {
      label: '温度',
      special: true,
      units: [
        { id: 'c', name: '摄氏度 (°C)' },
        { id: 'f', name: '华氏度 (°F)' },
        { id: 'k', name: '开尔文 (K)' }
      ],
      def: ['c', 'f'],
      allowNegative: true
    }
  };

  var NUM_RE = /^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$/;

  /* ---------------- 温度换算（以摄氏度为基准） ---------------- */
  function toCelsius(v, id) {
    if (id === 'c') return v;
    if (id === 'f') return (v - 32) * 5 / 9;
    return v - 273.15;            /* 开尔文 */
  }
  function fromCelsius(c, id) {
    if (id === 'c') return c;
    if (id === 'f') return c * 9 / 5 + 32;
    return c + 273.15;            /* 开尔文 */
  }

  function convert(cat, v, fromId, toId) {
    var cfg = DATA[cat];
    if (cfg.special) return fromCelsius(toCelsius(v, fromId), toId);
    var fu = findUnit(cfg, fromId), tu = findUnit(cfg, toId);
    return v * fu.f / tu.f;
  }

  function findUnit(cfg, id) {
    for (var i = 0; i < cfg.units.length; i++) {
      if (cfg.units[i].id === id) return cfg.units[i];
    }
    return null;
  }

  /* ---------------- 数值格式化：不产生无意义长小数 ---------------- */
  function fmt(n) {
    if (typeof n !== 'number' || !isFinite(n)) return '—';
    if (n === 0) return '0';
    var abs = Math.abs(n);
    if (abs >= 1e15 || abs < 1e-6) {
      var parts = n.toExponential(6).split('e');
      var mant = parts[0].replace(/\.?0+$/, '');
      return mant + 'e' + parts[1];
    }
    return Number(n.toPrecision(10)).toString();
  }

  /* ---------------- DOM ---------------- */
  var tabs     = Array.prototype.slice.call(document.querySelectorAll('.tab'));
  var panel    = document.getElementById('panel');
  var input    = document.getElementById('value');
  var fromSel  = document.getElementById('from');
  var toSel    = document.getElementById('to');
  var swapBtn  = document.getElementById('swap');
  var errEl    = document.getElementById('err');
  var primary  = document.getElementById('primary');
  var note     = document.getElementById('note');
  var allList  = document.getElementById('allList');

  var state = { cat: 'length' };

  function setError(msg) {
    errEl.textContent = msg || '';
    if (msg) input.setAttribute('aria-invalid', 'true');
    else input.removeAttribute('aria-invalid');
  }

  function unitName(id) {
    var u = findUnit(DATA[state.cat], id);
    return u ? u.name : id;
  }

  function fillSelects(cfg) {
    fromSel.textContent = '';
    toSel.textContent = '';
    cfg.units.forEach(function (u) {
      fromSel.appendChild(new Option(u.name, u.id));
      toSel.appendChild(new Option(u.name, u.id));
    });
    fromSel.value = cfg.def[0];
    toSel.value = cfg.def[1];
  }

  function clearOutputs() {
    primary.textContent = '—';
    primary.classList.add('empty');
    note.textContent = '';
    allList.textContent = '';
  }

  function render() {
    var cfg = DATA[state.cat];
    var raw = input.value.trim();

    if (raw === '') {
      setError('');
      clearOutputs();
      return;
    }
    if (!NUM_RE.test(raw)) {
      setError('“' + clip(raw) + '” 不是有效数字，请输入如 1、3.5、-40 这样的数值。');
      clearOutputs();
      return;
    }
    var v = Number(raw);
    if (!isFinite(v)) {
      setError('数值超出可计算范围。');
      clearOutputs();
      return;
    }
    if (!cfg.allowNegative && v < 0) {
      setError(cfg.negMsg);
      clearOutputs();
      return;
    }

    var fromId = fromSel.value;
    var toId   = toSel.value;
    var out    = convert(state.cat, v, fromId, toId);

    if (!isFinite(out)) {
      setError('换算结果超出可表示范围。');
      clearOutputs();
      return;
    }

    setError('');
    primary.classList.remove('empty');
    primary.textContent = fmt(v) + ' ' + unitName(fromId) + ' = ' + fmt(out) + ' ' + unitName(toId);

    /* 温度：低于绝对零度只作提示，不做数学阻断 */
    var n = '';
    if (cfg.special) {
      var kelvin = fromCelsius(toCelsius(v, fromId), 'k');
      if (kelvin < -1e-9) {
        n = '提示：该温度低于绝对零度（0 K / -273.15 °C），现实中不可达，此处仅为数学换算。';
      }
    }
    note.textContent = n;

    /* 全部单位等值 */
    allList.textContent = '';
    cfg.units.forEach(function (u) {
      var val = convert(state.cat, v, fromId, u.id);
      var li = document.createElement('li');
      if (u.id === fromId) li.className = 'dim';
      var a = document.createElement('span');
      a.className = 'u';
      a.textContent = u.name;
      var b = document.createElement('span');
      b.className = 'v';
      b.textContent = fmt(val);
      li.appendChild(a);
      li.appendChild(b);
      allList.appendChild(li);
    });
  }

  function clip(s) {
    return s.length > 24 ? s.slice(0, 24) + '…' : s;
  }

  function setCategory(cat) {
    state.cat = cat;
    tabs.forEach(function (t) {
      var on = t.dataset.cat === cat;
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      t.classList.toggle('on', on);
      t.tabIndex = on ? 0 : -1;
    });
    panel.setAttribute('aria-labelledby', 'tab-' + cat);
    fillSelects(DATA[cat]);
    render();
  }

  /* ---------------- 事件 ---------------- */
  tabs.forEach(function (t) {
    t.addEventListener('click', function () { setCategory(t.dataset.cat); });
  });

  /* 标签页方向键导航（键盘可完成全部操作） */
  document.querySelector('.tabs').addEventListener('keydown', function (e) {
    var i = tabs.indexOf(document.activeElement);
    if (i < 0) return;
    var ni = null;
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') ni = (i + 1) % tabs.length;
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') ni = (i - 1 + tabs.length) % tabs.length;
    else if (e.key === 'Home') ni = 0;
    else if (e.key === 'End') ni = tabs.length - 1;
    if (ni === null) return;
    e.preventDefault();
    tabs[ni].focus();
    setCategory(tabs[ni].dataset.cat);
  });

  input.addEventListener('input', render);
  input.addEventListener('change', render);
  fromSel.addEventListener('change', render);
  toSel.addEventListener('change', render);

  swapBtn.addEventListener('click', function () {
    var a = fromSel.value;
    fromSel.value = toSel.value;
    toSel.value = a;
    render();
  });

  /* ---------------- 初始化 ---------------- */
  setCategory('length');
})();
