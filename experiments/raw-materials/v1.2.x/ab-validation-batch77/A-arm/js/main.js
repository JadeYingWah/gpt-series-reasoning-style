/* ============================================
   个人作品集网站 - 主脚本
   功能：导航、表单验证、项目筛选、滚动动画
   ============================================ */

(function () {
    'use strict';

    // --- 移动端导航切换 ---
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');

    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function () {
            const isExpanded = hamburger.getAttribute('aria-expanded') === 'true';
            hamburger.setAttribute('aria-expanded', String(!isExpanded));
            navMenu.classList.toggle('active');
        });

        // 点击导航链接后关闭菜单（移动端）
        navMenu.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                if (window.innerWidth < 768) {
                    navMenu.classList.remove('active');
                    hamburger.setAttribute('aria-expanded', 'false');
                }
            });
        });
    }

    // --- 平滑滚动（锚点链接） ---
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // --- 项目筛选 ---
    const filterBtns = document.querySelectorAll('.filter-btn');
    const projectCards = document.querySelectorAll('.project-card');

    if (filterBtns.length > 0 && projectCards.length > 0) {
        filterBtns.forEach(function (btn) {
            btn.addEventListener('click', function () {
                // 更新按钮状态
                filterBtns.forEach(function (b) {
                    b.classList.remove('active');
                    b.setAttribute('aria-pressed', 'false');
                });
                btn.classList.add('active');
                btn.setAttribute('aria-pressed', 'true');

                // 筛选项目
                const filter = btn.dataset.filter;
                projectCards.forEach(function (card) {
                    const category = card.dataset.category;
                    if (filter === 'all' || category === filter) {
                        card.style.display = '';
                        // 触发重绘动画
                        card.style.opacity = '0';
                        requestAnimationFrame(function () {
                            card.style.opacity = '1';
                        });
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
        });
    }

    // --- 表单验证 ---
    const contactForm = document.getElementById('contactForm');

    if (contactForm) {
        const nameInput = document.getElementById('name');
        const emailInput = document.getElementById('email');
        const messageInput = document.getElementById('message');

        // 验证函数
        function validateField(input, validator) {
            const formGroup = input.closest('.form-group');
            const isValid = validator(input.value.trim());

            if (isValid) {
                formGroup.classList.remove('error');
            } else {
                formGroup.classList.add('error');
            }
            return isValid;
        }

        // 姓名验证：非空，至少2个字符
        function validateName(value) {
            return value.length >= 2;
        }

        // 邮箱验证：标准邮箱格式
        function validateEmail(value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(value);
        }

        // 消息验证：非空，至少10个字符
        function validateMessage(value) {
            return value.length >= 10;
        }

        // 失焦时验证
        if (nameInput) {
            nameInput.addEventListener('blur', function () {
                validateField(nameInput, validateName);
            });
        }
        if (emailInput) {
            emailInput.addEventListener('blur', function () {
                validateField(emailInput, validateEmail);
            });
        }
        if (messageInput) {
            messageInput.addEventListener('blur', function () {
                validateField(messageInput, validateMessage);
            });
        }

        // 提交时验证
        contactForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const isNameValid = validateField(nameInput, validateName);
            const isEmailValid = validateField(emailInput, validateEmail);
            const isMessageValid = validateField(messageInput, validateMessage);

            if (isNameValid && isEmailValid && isMessageValid) {
                // 模拟提交（实际项目中应发送到服务器）
                const submitBtn = contactForm.querySelector('button[type="submit"]');
                const originalText = submitBtn.textContent;
                submitBtn.textContent = '发送中...';
                submitBtn.disabled = true;

                setTimeout(function () {
                    alert('消息已发送！感谢您的联系，我会尽快回复。');
                    contactForm.reset();
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                }, 1000);
            } else {
                // 聚焦到第一个错误字段
                const firstError = contactForm.querySelector('.form-group.error input, .form-group.error textarea');
                if (firstError) {
                    firstError.focus();
                }
            }
        });
    }

    // --- 滚动动画（Intersection Observer） ---
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.fade-in').forEach(function (el) {
        observer.observe(el);
    });

    // --- 导航栏滚动效果 ---
    let lastScroll = 0;
    const navbar = document.querySelector('.navbar');

    if (navbar) {
        window.addEventListener('scroll', function () {
            const currentScroll = window.pageYOffset;

            if (currentScroll > 100) {
                navbar.style.boxShadow = '0 2px 20px rgba(0,0,0,0.3)';
            } else {
                navbar.style.boxShadow = 'none';
            }

            lastScroll = currentScroll;
        }, { passive: true });
    }

    // --- 页脚年份自动更新 ---
    const yearElement = document.getElementById('currentYear');
    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }

    // --- 页面加载完成标记 ---
    document.addEventListener('DOMContentLoaded', function () {
        document.body.setAttribute('data-loaded', 'true');
    });

})();
