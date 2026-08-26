/**
 * home.js — Home page logic
 *
 * Loads blog information dynamically from Supabase Storage
 * through blogs-data.js.
 */

document.addEventListener('DOMContentLoaded', () => {
    initNav();
    initParticles();

    // Run independently so one failing operation
    // does not block the other.
    loadStats();
    loadRecentPosts();
});


/* ─────────────────────────────────────────────────────────
   Navigation
   ───────────────────────────────────────────────────────── */

function initNav() {
    const navbar = document.getElementById('navbar');
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.getElementById('navLinks');

    if (navbar) {
        window.addEventListener('scroll', () => {
            navbar.classList.toggle(
                'scrolled',
                window.scrollY > 30
            );
        });
    }

    if (hamburger) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('open');

            if (navLinks) {
                navLinks.classList.toggle('open');
            }
        });
    }
}


/* ─────────────────────────────────────────────────────────
   Statistics
   ───────────────────────────────────────────────────────── */

async function loadStats() {
    const totalElement = document.querySelector(
        '#totalBlogs .stat-num'
    );

    if (!totalElement) {
        console.warn(
            '[BlogBoard] #totalBlogs .stat-num not found.'
        );
        return;
    }

    // Show a temporary loading state.
    totalElement.textContent = '...';

    try {
        if (
            typeof getTotalCount !== 'function'
        ) {
            throw new Error(
                'getTotalCount() is not available. Check blogs-data.js.'
            );
        }

        const total = await getTotalCount();

        console.log(
            '[BlogBoard] Home page total articles:',
            total
        );

        animateCounter(
            'totalBlogs',
            total
        );

    } catch (error) {
        console.error(
            '[BlogBoard] Failed to load article count:',
            error
        );

        totalElement.textContent = '0';
    }
}


/* ─────────────────────────────────────────────────────────
   Counter Animation
   ───────────────────────────────────────────────────────── */

function animateCounter(id, target) {
    const container =
        document.getElementById(id);

    if (!container) {
        return;
    }

    const element =
        container.querySelector('.stat-num') ||
        container;

    target = Number(target);

    if (!Number.isFinite(target)) {
        target = 0;
    }

    target = Math.max(
        0,
        Math.floor(target)
    );

    // Immediately show 0.
    if (target === 0) {
        element.textContent = '0';
        return;
    }

    let current = 0;

    const duration = 800;
    const interval = 30;
    const steps = Math.ceil(
        duration / interval
    );

    const increment =
        Math.max(
            1,
            Math.ceil(target / steps)
        );

    const timer = setInterval(() => {
        current += increment;

        if (current >= target) {
            current = target;
            clearInterval(timer);
        }

        element.textContent =
            String(current);

    }, interval);
}


/* ─────────────────────────────────────────────────────────
   Recent Posts
   ───────────────────────────────────────────────────────── */

async function loadRecentPosts() {
    const container =
        document.getElementById('recentPosts');

    if (!container) {
        console.warn(
            '[BlogBoard] #recentPosts not found.'
        );
        return;
    }

    // Keep the existing loading UI.
    container.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>Loading posts…</p>
        </div>
    `;

    try {
        if (
            typeof getRecentBlogs !== 'function'
        ) {
            throw new Error(
                'getRecentBlogs() is not available. Check blogs-data.js.'
            );
        }

        /*
         * IMPORTANT:
         *
         * Do not wait forever for Supabase.
         * If getRecentBlogs() does not respond within
         * 10 seconds, show an error instead.
         */
        const recentPosts =
            await withTimeout(
                getRecentBlogs(6),
                10000
            );

        console.log(
            '[BlogBoard] Latest articles loaded:',
            recentPosts
        );

        if (
            !Array.isArray(recentPosts) ||
            recentPosts.length === 0
        ) {
            container.innerHTML = `
                <p style="color:var(--text-muted);padding:20px">
                    No articles published yet.
                    Check back soon!
                </p>
            `;

            return;
        }

        const cards = recentPosts
            .map(blog => {

                /*
                 * Get category metadata.
                 */
                const meta =
                    CATEGORY_META &&
                    CATEGORY_META[blog.category];

                /*
                 * If category metadata is missing,
                 * still allow the article to display.
                 */
                const categoryLabel =
                    meta
                        ? meta.shortLabel
                        : (
                            blog.category ||
                            'Article'
                        );

                const categoryColor =
                    meta
                        ? meta.color
                        : '#7c6af7';

                const categoryBg =
                    meta
                        ? meta.bgColor
                        : 'rgba(124, 106, 247, 0.12)';

                /*
                 * Determine article ID.
                 */
                const blogId =
                    blog.id ||
                    blog.file ||
                    blog.slug ||
                    '';

                /*
                 * Do not create a broken link.
                 */
                if (!blogId) {
                    console.warn(
                        '[BlogBoard] Article has no ID:',
                        blog
                    );
                }

                return `
                    <a
                        href="post.html#id=${encodeURIComponent(blogId)}"
                        class="recent-card"
                    >

                        <div class="recent-card-meta">

                            <span
                                class="recent-cat-badge"
                                style="
                                    background:${categoryBg};
                                    color:${categoryColor};
                                "
                            >
                                ${escapeHtml(categoryLabel)}
                            </span>

                            <span class="recent-date">
                                ${escapeHtml(
                                    formatDate(blog.date)
                                )}
                            </span>

                        </div>

                        <h3 class="recent-title">
                            ${escapeHtml(
                                blog.title ||
                                'Untitled Article'
                            )}
                        </h3>

                        <p class="recent-desc">
                            ${escapeHtml(
                                blog.description ||
                                ''
                            )}
                        </p>

                        <span class="recent-readtime">
                            📖
                            ${escapeHtml(
                                blog.readTime ||
                                '5 min'
                            )}
                            read
                        </span>

                    </a>
                `;
            })
            .filter(Boolean)
            .join('');

        if (!cards) {
            container.innerHTML = `
                <p style="color:var(--text-muted);padding:20px">
                    No valid articles found.
                </p>
            `;
            return;
        }

        container.innerHTML = cards;

    } catch (error) {
        console.error(
            '[BlogBoard] Failed to load latest articles:',
            error
        );

        container.innerHTML = `
            <div
                style="
                    color:var(--text-muted);
                    padding:20px;
                    text-align:center;
                "
            >
                <p>
                    Unable to load latest articles.
                </p>

                <button
                    type="button"
                    onclick="loadRecentPosts()"
                    style="
                        margin-top:10px;
                        padding:8px 16px;
                        cursor:pointer;
                    "
                >
                    Try Again
                </button>
            </div>
        `;
    }
}


/* ─────────────────────────────────────────────────────────
   Promise Timeout
   ───────────────────────────────────────────────────────── */

function withTimeout(
    promise,
    timeout = 10000
) {
    return Promise.race([
        promise,

        new Promise((_, reject) => {
            setTimeout(() => {
                reject(
                    new Error(
                        `Request timed out after ${timeout / 1000} seconds.`
                    )
                );
            }, timeout);
        })
    ]);
}


/* ─────────────────────────────────────────────────────────
   HTML Escaping
   ───────────────────────────────────────────────────────── */

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}


/* ─────────────────────────────────────────────────────────
   Particle Background
   ───────────────────────────────────────────────────────── */

function initParticles() {
    const canvas =
        document.getElementById(
            'particleCanvas'
        );

    if (!canvas) {
        return;
    }

    const ctx =
        canvas.getContext('2d');

    if (!ctx) {
        return;
    }

    let W = 0;
    let H = 0;

    const particles = [];


    /* ── Resize Canvas ── */

    function resize() {
        W = canvas.offsetWidth;
        H = canvas.offsetHeight;

        /*
         * Prevent zero-size canvas.
         */
        if (W <= 0) {
            W = window.innerWidth;
        }

        if (H <= 0) {
            H = window.innerHeight;
        }

        canvas.width = W;
        canvas.height = H;
    }

    resize();

    window.addEventListener(
        'resize',
        resize
    );


    /* ── Create Particles ── */

    const PARTICLE_COUNT = 60;

    for (
        let i = 0;
        i < PARTICLE_COUNT;
        i++
    ) {
        particles.push({
            x: Math.random() * W,
            y: Math.random() * H,

            r:
                Math.random() * 1.5 +
                0.5,

            vx:
                (Math.random() - 0.5) *
                0.4,

            vy:
                (Math.random() - 0.5) *
                0.4,

            a:
                Math.random() * 0.5 +
                0.1
        });
    }


    /* ── Draw Particles ── */

    function draw() {
        /*
         * Do not draw if the canvas has
         * no usable dimensions.
         */
        if (W <= 0 || H <= 0) {
            requestAnimationFrame(draw);
            return;
        }

        ctx.clearRect(
            0,
            0,
            W,
            H
        );


        /* ── Move and draw particles ── */

        particles.forEach(
            particle => {

                particle.x =
                    (
                        particle.x +
                        particle.vx +
                        W
                    ) % W;

                particle.y =
                    (
                        particle.y +
                        particle.vy +
                        H
                    ) % H;


                ctx.beginPath();

                ctx.arc(
                    particle.x,
                    particle.y,
                    particle.r,
                    0,
                    Math.PI * 2
                );

                ctx.fillStyle =
                    `rgba(
                        124,
                        106,
                        247,
                        ${particle.a}
                    )`;

                ctx.fill();
            }
        );


        /* ── Draw connecting lines ── */

        for (
            let i = 0;
            i < particles.length;
            i++
        ) {

            for (
                let j = i + 1;
                j < particles.length;
                j++
            ) {

                const dx =
                    particles[i].x -
                    particles[j].x;

                const dy =
                    particles[i].y -
                    particles[j].y;

                const distance =
                    Math.sqrt(
                        dx * dx +
                        dy * dy
                    );


                if (distance < 100) {

                    ctx.beginPath();

                    ctx.moveTo(
                        particles[i].x,
                        particles[i].y
                    );

                    ctx.lineTo(
                        particles[j].x,
                        particles[j].y
                    );

                    ctx.strokeStyle =
                        `rgba(
                            124,
                            106,
                            247,
                            ${
                                0.12 *
                                (
                                    1 -
                                    distance / 100
                                )
                            }
                        )`;

                    ctx.lineWidth = 0.5;

                    ctx.stroke();
                }
            }
        }

        requestAnimationFrame(draw);
    }


    draw();
}