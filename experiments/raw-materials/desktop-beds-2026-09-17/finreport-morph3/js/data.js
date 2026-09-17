/**
 * 个人财务 2025 年 12 个月模拟数据 — 全项目唯一数据源
 * 仪表盘与报告页必须读取本文件；禁止页面手写第二套数字。
 */
(function (global) {
  "use strict";

  var YEAR = 2025;
  var CURRENCY = "CNY";

  var INCOME_CATEGORIES = ["主业", "兼职", "理财", "其他收入"];
  var EXPENSE_CATEGORIES = [
    "餐饮",
    "房租",
    "交通",
    "购物",
    "娱乐",
    "医疗",
    "教育",
    "日用",
    "通讯",
    "其他支出"
  ];

  /**
   * 每月原始分项（单位：元）。
   * 结构: { month, income: {类别:金额}, expense: {类别:金额} }
   * 缺省类别视为 0。
   */
  var MONTHLY = [
    {
      month: 1,
      income: { 主业: 12800, 兼职: 1800, 理财: 320, 其他收入: 0 },
      expense: { 餐饮: 3200, 房租: 4200, 交通: 380, 购物: 1600, 娱乐: 680, 医疗: 0, 教育: 0, 日用: 520, 通讯: 99, 其他支出: 200 }
    },
    {
      month: 2,
      income: { 主业: 12800, 兼职: 0, 理财: 280, 其他收入: 1500 },
      expense: { 餐饮: 4200, 房租: 4200, 交通: 620, 购物: 2800, 娱乐: 1200, 医疗: 0, 教育: 0, 日用: 480, 通讯: 99, 其他支出: 600 }
    },
    {
      month: 3,
      income: { 主业: 12800, 兼职: 2200, 理财: 350, 其他收入: 0 },
      expense: { 餐饮: 3000, 房租: 4200, 交通: 420, 购物: 900, 娱乐: 550, 医疗: 0, 教育: 800, 日用: 500, 通讯: 99, 其他支出: 150 }
    },
    {
      month: 4,
      income: { 主业: 13200, 兼职: 1500, 理财: 310, 其他收入: 0 },
      expense: { 餐饮: 3100, 房租: 4200, 交通: 400, 购物: 1100, 娱乐: 720, 医疗: 260, 教育: 0, 日用: 530, 通讯: 99, 其他支出: 180 }
    },
    {
      month: 5,
      income: { 主业: 13200, 兼职: 2800, 理财: 340, 其他收入: 500 },
      expense: { 餐饮: 3300, 房租: 4200, 交通: 480, 购物: 1400, 娱乐: 980, 医疗: 0, 教育: 0, 日用: 510, 通讯: 99, 其他支出: 220 }
    },
    {
      month: 6,
      income: { 主业: 13200, 兼职: 2000, 理财: 360, 其他收入: 0 },
      expense: { 餐饮: 3400, 房租: 4200, 交通: 450, 购物: 1800, 娱乐: 1100, 医疗: 0, 教育: 1200, 日用: 540, 通讯: 99, 其他支出: 200 }
    },
    {
      month: 7,
      income: { 主业: 13600, 兼职: 1200, 理财: 330, 其他收入: 800 },
      expense: { 餐饮: 3600, 房租: 4200, 交通: 520, 购物: 2200, 娱乐: 1500, 医疗: 380, 教育: 0, 日用: 560, 通讯: 99, 其他支出: 300 }
    },
    {
      month: 8,
      income: { 主业: 13600, 兼职: 2600, 理财: 370, 其他收入: 0 },
      expense: { 餐饮: 3500, 房租: 4200, 交通: 600, 购物: 1600, 娱乐: 1300, 医疗: 0, 教育: 900, 日用: 520, 通讯: 99, 其他支出: 180 }
    },
    {
      month: 9,
      income: { 主业: 13600, 兼职: 1800, 理财: 350, 其他收入: 0 },
      expense: { 餐饮: 3000, 房租: 4200, 交通: 390, 购物: 950, 娱乐: 600, 医疗: 0, 教育: 1500, 日用: 500, 通讯: 99, 其他支出: 160 }
    },
    {
      month: 10,
      income: { 主业: 13600, 兼职: 2400, 理财: 340, 其他收入: 600 },
      expense: { 餐饮: 3200, 房租: 4200, 交通: 430, 购物: 1300, 娱乐: 850, 医疗: 0, 教育: 0, 日用: 510, 通讯: 99, 其他支出: 190 }
    },
    {
      month: 11,
      income: { 主业: 14000, 兼职: 1600, 理财: 380, 其他收入: 0 },
      expense: { 餐饮: 3100, 房租: 4200, 交通: 410, 购物: 1700, 娱乐: 700, 医疗: 520, 教育: 0, 日用: 530, 通讯: 99, 其他支出: 210 }
    },
    {
      month: 12,
      income: { 主业: 18000, 兼职: 2000, 理财: 420, 其他收入: 2000 },
      expense: { 餐饮: 3800, 房租: 4200, 交通: 550, 购物: 3200, 娱乐: 1600, 医疗: 0, 教育: 0, 日用: 600, 通讯: 99, 其他支出: 450 }
    }
  ];

  function sumKeys(obj, keys) {
    var total = 0;
    for (var i = 0; i < keys.length; i++) {
      total += Number(obj[keys[i]] || 0);
    }
    return total;
  }

  function monthLabel(m) {
    return m < 10 ? "0" + m : String(m);
  }

  /** 补全字段并计算每月合计 */
  function normalize() {
    return MONTHLY.map(function (row) {
      var income = {};
      var expense = {};
      INCOME_CATEGORIES.forEach(function (c) {
        income[c] = Number(row.income[c] || 0);
      });
      EXPENSE_CATEGORIES.forEach(function (c) {
        expense[c] = Number(row.expense[c] || 0);
      });
      var totalIncome = sumKeys(income, INCOME_CATEGORIES);
      var totalExpense = sumKeys(expense, EXPENSE_CATEGORIES);
      return {
        month: row.month,
        label: yearMonthLabel(row.month),
        shortLabel: monthLabel(row.month) + "月",
        income: income,
        expense: expense,
        totalIncome: totalIncome,
        totalExpense: totalExpense,
        net: totalIncome - totalExpense
      };
    });
  }

  function yearMonthLabel(m) {
    return YEAR + "-" + monthLabel(m);
  }

  var months = normalize();

  function sumMonths(key) {
    return months.reduce(function (acc, m) {
      return acc + m[key];
    }, 0);
  }

  function categoryTotals(side) {
    var keys = side === "income" ? INCOME_CATEGORIES : EXPENSE_CATEGORIES;
    var totals = {};
    keys.forEach(function (k) {
      totals[k] = months.reduce(function (acc, m) {
        return acc + m[side][k];
      }, 0);
    });
    return totals;
  }

  var summary = {
    year: YEAR,
    currency: CURRENCY,
    monthCount: months.length,
    totalIncome: sumMonths("totalIncome"),
    totalExpense: sumMonths("totalExpense"),
    totalNet: sumMonths("net"),
    avgIncome: round2(sumMonths("totalIncome") / months.length),
    avgExpense: round2(sumMonths("totalExpense") / months.length),
    avgNet: round2(sumMonths("net") / months.length),
    savingsRate: ratio(sumMonths("net"), sumMonths("totalIncome")),
    incomeByCategory: categoryTotals("income"),
    expenseByCategory: categoryTotals("expense")
  };

  function round2(n) {
    return Math.round(n * 100) / 100;
  }

  function ratio(a, b) {
    if (!b) return 0;
    return round2((a / b) * 100);
  }

  var FinanceData = {
    year: YEAR,
    currency: CURRENCY,
    incomeCategories: INCOME_CATEGORIES.slice(),
    expenseCategories: EXPENSE_CATEGORIES.slice(),
    months: months,
    summary: summary,
    formatMoney: function (n) {
      var v = round2(Number(n) || 0);
      return v.toLocaleString("zh-CN", { minimumFractionDigits: 0, maximumFractionDigits: 2 });
    },
    formatMoneyWan: function (n) {
      var v = (Number(n) || 0) / 10000;
      return (Math.round(v * 100) / 100).toFixed(2);
    }
  };

  global.FinanceData = FinanceData;
})(typeof window !== "undefined" ? window : globalThis);
