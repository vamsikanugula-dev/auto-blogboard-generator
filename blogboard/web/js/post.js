/**
 * post.js — Blog post viewer with markdown rendering
 *
 * Uses:
 *   window.location.hash (#id=...)
 *
 * Article content is loaded from:
 *   Supabase Storage
 */

document.addEventListener('DOMContentLoaded', () => {
    initNav();
    loadPost();
    initReadingProgress();
});


/* ─────────────────────────────────────────────
   Parse hash params
   ───────────────────────────────────────────── */

function getHashParam(key) {
    // Supports:
    // #id=foo
    // #cat=ml&id=foo

    const hash = window.location.hash.replace(/^#/, '');
    const params = new URLSearchParams(hash);

    return params.get(key);
}


/* ─────────────────────────────────────────────
   Navigation
   ───────────────────────────────────────────── */

function initNav() {
    const navbar = document.getElementById('navbar');
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.getElementById('navLinks');

    window.addEventListener('scroll', () => {
        if (navbar) {
            navbar.classList.toggle(
                'scrolled',
                window.scrollY > 30
            );
        }
    });

    hamburger?.addEventListener('click', () => {
        hamburger.classList.toggle('open');
        navLinks?.classList.toggle('open');
    });
}


/* ─────────────────────────────────────────────
   Reading Progress
   ───────────────────────────────────────────── */

function initReadingProgress() {
    const bar = document.getElementById('readingProgress');

    if (!bar) {
        return;
    }

    window.addEventListener('scroll', () => {
        const doc = document.documentElement;

        const scrollTop =
            doc.scrollTop || document.body.scrollTop;

        const scrollHeight =
            doc.scrollHeight - doc.clientHeight;

        const progress =
            scrollHeight > 0
                ? (scrollTop / scrollHeight) * 100
                : 0;

        bar.style.width = `${progress}%`;
    });
}


/* ─────────────────────────────────────────────
   Load Blog Post
   ───────────────────────────────────────────── */

async function loadPost() {

    // Example:
    // post.html#id=blogs/ml/time-series-forecasting-models.md

    const rawId = getHashParam('id');

    const id = rawId
        ? decodeURIComponent(rawId)
        : null;

    const contentEl =
        document.getElementById('postContent');

    /*
     * No article ID
     */
    if (!id) {
        window.location.replace('index.html');
        return;
    }

    /*
     * Find article metadata
     */
    const blog = await getBlogById(id);

    if (!blog) {
        showError(
            'Post not found. It may have been removed or the link is incorrect.',
            contentEl
        );

        return;
    }

    /*
     * Category metadata
     */
    const meta =
        CATEGORY_META[blog.category] || {
            label: blog.category,
            shortLabel: blog.category
        };


    /* ─────────────────────────────────────────
       Page title
       ───────────────────────────────────────── */

    document.title =
        `${blog.title} — BlogBoard`;


    /* ─────────────────────────────────────────
       Breadcrumb
       ───────────────────────────────────────── */

    const catLink =
        document.getElementById('catLink');

    if (catLink) {
        catLink.textContent = meta.label;

        catLink.href =
            `category.html#cat=${blog.category}`;
    }


    const postTitleSpan =
        document.getElementById('postTitle');

    if (postTitleSpan) {
        postTitleSpan.textContent = blog.title;
    }


    /* ─────────────────────────────────────────
       Header
       ───────────────────────────────────────── */

    const titleElement =
        document.getElementById('postTitleH1');

    if (titleElement) {
        titleElement.textContent = blog.title;
    }


    const dateElement =
        document.getElementById('postDate');

    if (dateElement) {
        dateElement.textContent =
            formatDate(blog.date);
    }


    /* ─────────────────────────────────────────
       Category badge
       ───────────────────────────────────────── */

    const catBadge =
        document.getElementById('postCatBadge');

    if (catBadge) {

        catBadge.textContent =
            meta.shortLabel;

        catBadge.className =
            `post-cat-badge badge-${blog.category}`;
    }


    /* ─────────────────────────────────────────
       Reading time
       ───────────────────────────────────────── */

    const readTimeEl =
        document.getElementById('postReadTime');

    if (readTimeEl) {

        readTimeEl.textContent =
            `📖 ${blog.readTime} read`;
    }


    /* ─────────────────────────────────────────
       Active navigation link
       ───────────────────────────────────────── */

    document
        .querySelectorAll('.nav-link[href]')
        .forEach(link => {

            if (
                link.href.includes(
                    `cat=${blog.category}`
                )
            ) {
                link.classList.add('active');
            }
        });


    /* ─────────────────────────────────────────
       Back button
       ───────────────────────────────────────── */

    const backBtn =
        document.getElementById('backToCat');

    if (backBtn) {

        backBtn.href =
            `category.html#cat=${blog.category}`;

        backBtn.textContent =
            `← Back to ${meta.shortLabel}`;
    }


    /* ─────────────────────────────────────────
       Tags
       ───────────────────────────────────────── */

    const tagsEl =
        document.getElementById('postTags');

    if (
        tagsEl &&
        blog.tags?.length
    ) {

        tagsEl.innerHTML =
            blog.tags
                .map(
                    tag =>
                        `<span class="post-tag">#${tag}</span>`
                )
                .join('');
    }


    /* ─────────────────────────────────────────
       Load Markdown from Supabase Storage
       ───────────────────────────────────────── */

    try {

        /*
         * Read Supabase Storage URL from config.js
         */
        const storageUrl =
            window.CONFIG?.SUPABASE_STORAGE_URL;


        /*
         * Make sure config.js loaded correctly
         */
        if (!storageUrl) {

            throw new Error(
                'Supabase Storage URL is not configured.'
            );
        }


        /*
         * Construct article URL
         *
         * Example:
         *
         * https://...supabase.co/storage/v1/object/public/blogboard
         * /blogs/ml/time-series-forecasting-models.md
         */
        const articleUrl =
            `${storageUrl}/${blog.file}`;


        console.log(
            '[BlogBoard] Loading article:',
            articleUrl
        );


        /*
         * Fetch Markdown
         */
        const response =
            await fetch(articleUrl);


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        /*
         * Read Markdown text
         */
        const mdText =
            await response.text();


        /*
         * Render Markdown
         */
        renderMarkdown(
            mdText,
            contentEl
        );


        /*
         * Build Table of Contents
         */
        buildTOC();


    } catch (err) {

        const storageUrl =
            window.CONFIG?.SUPABASE_STORAGE_URL ||
            'NOT_CONFIGURED';


        const expectedUrl =
            `${storageUrl}/${blog.file}`;


        showError(
            `Could not load the article file.<br>

            <small>
                Expected URL:
                <code>${expectedUrl}</code>
            </small><br>

            <small>
                Make sure your Supabase Storage bucket
                is public and the storage URL in
                config.js is correct.
            </small>`,
            contentEl
        );


        console.error(
            '[BlogBoard] Failed to load blog post:',
            err
        );
    }
}


/* ─────────────────────────────────────────────
   Render Markdown
   ───────────────────────────────────────────── */

function renderMarkdown(
    mdText,
    container
) {

    if (!container) {
        return;
    }


    /*
     * Configure marked
     */
    marked.setOptions({
        gfm: true,
        breaks: true
    });


    /*
     * Create renderer
     */
    const renderer =
        new marked.Renderer();


    /*
     * Add IDs to headings
     */
    renderer.heading = (
        text,
        level
    ) => {

        const rawText =
            typeof text === 'object'
                ? text.text
                : text;


        const escapedText =
            rawText
                .toLowerCase()
                .replace(/[^\w]+/g, '-')
                .replace(/^-+|-+$/g, '');


        return `
            <h${level} id="${escapedText}">
                ${rawText}
            </h${level}>
        `;
    };


    /*
     * Convert Markdown → HTML
     */
    container.innerHTML =
        marked.parse(
            mdText,
            { renderer }
        );


    /* ─────────────────────────────────────────
       Syntax highlighting
       ───────────────────────────────────────── */

    if (window.hljs) {

        container
            .querySelectorAll('pre code')
            .forEach(block => {

                hljs.highlightElement(block);
            });
    }


    /* ─────────────────────────────────────────
       Copy buttons
       ───────────────────────────────────────── */

    container
        .querySelectorAll('pre')
        .forEach(pre => {

            const btn =
                document.createElement('button');


            btn.className =
                'copy-btn';


            btn.textContent =
                'Copy';


            btn.style.cssText = `
                position: absolute;
                top: 10px;
                right: 12px;

                background:
                    rgba(124,106,247,0.15);

                color: #a89cf7;

                border:
                    1px solid rgba(124,106,247,0.25);

                border-radius: 6px;

                padding: 3px 10px;

                font-size: 0.75rem;

                cursor: pointer;

                font-family:
                    var(--font-sans);

                transition:
                    all 0.15s;
            `;


            btn.addEventListener(
                'click',
                async () => {

                    const code =
                        pre.querySelector('code');


                    try {

                        await navigator.clipboard.writeText(
                            code?.textContent || ''
                        );


                        btn.textContent =
                            'Copied!';


                        setTimeout(() => {

                            btn.textContent =
                                'Copy';

                        }, 2000);


                    } catch (error) {

                        console.error(
                            'Failed to copy code:',
                            error
                        );
                    }
                }
            );


            pre.style.position =
                'relative';


            pre.appendChild(btn);
        });
}


/* ─────────────────────────────────────────────
   Build Table of Contents
   ───────────────────────────────────────────── */

function buildTOC() {

    const content =
        document.getElementById(
            'postContent'
        );


    const tocNav =
        document.getElementById(
            'tocNav'
        );


    if (
        !content ||
        !tocNav
    ) {
        return;
    }


    const headings =
        content.querySelectorAll(
            'h2, h3, h4'
        );


    if (headings.length === 0) {
        return;
    }


    tocNav.innerHTML = '';


    /*
     * Observe headings while scrolling
     */
    const observer =
        new IntersectionObserver(
            entries => {

                entries.forEach(entry => {

                    if (
                        entry.isIntersecting
                    ) {

                        tocNav
                            .querySelectorAll(
                                '.toc-link'
                            )
                            .forEach(link => {

                                link.classList.remove(
                                    'active'
                                );
                            });


                        const activeLink =
                            tocNav.querySelector(
                                `[data-target="${entry.target.id}"]`
                            );


                        activeLink?.classList.add(
                            'active'
                        );
                    }
                });
            },
            {
                rootMargin:
                    '-20% 0px -70% 0px'
            }
        );


    /*
     * Create TOC links
     */
    headings.forEach(heading => {

        const level =
            heading.tagName.toLowerCase();


        const link =
            document.createElement('a');


        link.href =
            `#${heading.id}`;


        link.setAttribute(
            'data-target',
            heading.id
        );


        link.textContent =
            heading.textContent;


        link.className =
            `toc-link level-${level}`;


        link.addEventListener(
            'click',
            event => {

                event.preventDefault();


                document
                    .getElementById(
                        heading.id
                    )
                    ?.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
            }
        );


        tocNav.appendChild(link);


        observer.observe(heading);
    });
}


/* ─────────────────────────────────────────────
   Error State
   ───────────────────────────────────────────── */

function showError(
    message,
    container
) {

    if (!container) {
        return;
    }


    container.innerHTML = `
        <div
            style="
                padding:40px;
                text-align:center;
                color:var(--text-muted)
            "
        >

            <div
                style="
                    font-size:2.5rem;
                    margin-bottom:16px
                "
            >
                ⚠️
            </div>


            <h3
                style="
                    color:var(--text-secondary);
                    margin-bottom:12px
                "
            >
                Unable to load article
            </h3>


            <p
                style="
                    line-height:1.7
                "
            >
                ${message}
            </p>

        </div>
    `;
}