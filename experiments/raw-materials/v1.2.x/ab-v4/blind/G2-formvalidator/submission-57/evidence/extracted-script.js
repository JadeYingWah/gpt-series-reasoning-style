
'use strict';
(function () {
  function fail(msg) { return { ok: false, msg: msg }; }
  function pass(msg) { return { ok: true, msg: msg }; }

  function validateEmail(raw) {
    var v = raw.trim();
    if (!v) return fail('邮箱不能为空');
    if (/\s/.test(v)) return fail('邮箱不能包含空格或换行');
    if (v.length > 254) return fail('邮箱过长：不能超过 254 个字符（当前 ' + v.length + ' 个）');
    var parts = v.split('@');
    if (parts.length !== 2) return fail('邮箱格式不正确：需包含且仅包含一个 @（例如 name@example.com）');
    var local = parts[0];
    var domain = parts[1];
    if (!local) return fail('邮箱格式不正确：@ 之前缺少内容');
    if (local.length > 64) return fail('邮箱 @ 之前的部分过长：不能超过 64 个字符');
    if (!/^[A-Za-z0-9._%+-]+$/.test(local)) return fail('邮箱 @ 之前含不支持的字符：仅允许字母、数字及 . _ % + -');
    if (!domain) return fail('邮箱格式不正确：@ 之后缺少域名');
    if (!/^[A-Za-z0-9.-]+$/.test(domain)) return fail('邮箱域名含不支持的字符');
    var domainOk = /^[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?)+$/.test(domain)
      && /\.[A-Za-z]{2,}$/.test(domain);
    if (!domainOk) return fail('邮箱域名格式不正确（例如 example.com）');
    return pass('✓ 邮箱格式正确');
  }

  function validatePhone(raw) {
    var v = raw.trim();
    if (!v) return fail('手机号不能为空');
    if (/\s/.test(v)) return fail('手机号不能包含空格');
    if (!/^\d+$/.test(v)) return fail('手机号只能包含数字（检测到非法字符）');
    if (v.length > 11) return fail('手机号超长：应为 11 位数字（当前 ' + v.length + ' 位）');
    if (v.length < 11) return fail('手机号位数不足：应为 11 位数字（当前 ' + v.length + ' 位）');
    if (!/^1[3-9]/.test(v)) return fail('手机号格式不正确：应以 1 开头，第 2 位为 3-9');
    return pass('✓ 手机号格式正确');
  }

  function validatePassword(raw) {
    var v = raw;
    if (!v) return fail('密码不能为空');
    if (v.length > 64) return fail('密码过长：不能超过 64 个字符（当前 ' + v.length + ' 个）');
    if (v.length < 8) return fail('密码长度不足：至少 8 位（当前 ' + v.length + ' 位）');
    var hasLetter = /[A-Za-z]/.test(v);
    var hasDigit = /\d/.test(v);
    if (!hasLetter && !hasDigit) return fail('密码必须同时包含字母和数字（当前两者都缺少）');
    if (!hasLetter) return fail('密码缺少字母：必须同时包含字母和数字');
    if (!hasDigit) return fail('密码缺少数字：必须同时包含字母和数字');
    return pass('✓ 密码可用（≥8 位，含字母与数字；允许特殊字符）');
  }

  var FIELDS = [
    { id: 'email', validate: validateEmail },
    { id: 'phone', validate: validatePhone },
    { id: 'password', validate: validatePassword }
  ];

  var form = document.getElementById('form');
  var banner = document.getElementById('banner');
  var touched = {};

  function applyResult(id, result) {
    var input = document.getElementById(id);
    var field = document.getElementById(id + '-field');
    var hint = document.getElementById(id + '-hint');
    field.classList.toggle('error', !result.ok);
    field.classList.toggle('success', result.ok);
    input.setAttribute('aria-invalid', result.ok ? 'false' : 'true');
    hint.textContent = result.msg;
  }

  function hideBanner() {
    banner.hidden = true;
    banner.textContent = '';
  }

  FIELDS.forEach(function (f) {
    var input = document.getElementById(f.id);
    touched[f.id] = false;
    input.addEventListener('blur', function () {
      touched[f.id] = true;
      applyResult(f.id, f.validate(input.value));
    });
    input.addEventListener('input', function () {
      hideBanner();
      if (touched[f.id]) applyResult(f.id, f.validate(input.value));
    });
  });

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var firstInvalid = null;
    FIELDS.forEach(function (f) {
      var input = document.getElementById(f.id);
      touched[f.id] = true;
      var result = f.validate(input.value);
      applyResult(f.id, result);
      if (!result.ok && !firstInvalid) firstInvalid = input;
    });
    if (firstInvalid) {
      hideBanner();
      firstInvalid.focus();
    } else {
      banner.textContent = '提交成功：邮箱、手机号、密码均校验通过（本地演示，未发送任何数据）';
      banner.hidden = false;
    }
  });
})();
