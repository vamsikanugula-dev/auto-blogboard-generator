/**
 * blogs-data.js — Dynamic Blog Registry
 *
 * Blog articles are stored in Supabase Storage:
 *
 *   blogs/{domain}/articles.json
 *   blogs/{domain}/{slug}.md
 *
 * This file is responsible for:
 * - Loading article metadata
 * - Loading recent articles
 * - Counting articles
 * - Finding individual articles
 * - Caching loaded data
 */


/* =========================================================
   CATEGORY METADATA
   ========================================================= */

const CATEGORY_META = {

    ml: {
        label: 'Machine Learning',
        shortLabel: 'ML',
        description:
            'Algorithms, theory, and applied ML from fundamentals to production.',
        icon: '🧠',
        color: '#7c6af7',
        bgColor: 'rgba(124, 106, 247, 0.12)'
    },

    dl: {
        label: 'Deep Learning',
        shortLabel: 'DL',
        description:
            'Neural networks, architectures, training tricks, and modern DL research.',
        icon: '🔬',
        color: '#4fc8b8',
        bgColor: 'rgba(79, 200, 184, 0.12)'
    },

    nlp: {
        label: 'Natural Language Processing',
        shortLabel: 'NLP',
        description:
            'Text processing, transformers, LLMs, and language understanding.',
        icon: '📝',
        color: '#e879a0',
        bgColor: 'rgba(232, 121, 160, 0.12)'
    },

    cv: {
        label: 'Computer Vision',
        shortLabel: 'CV',
        description:
            'Image processing, object detection, segmentation, and visual AI.',
        icon: '👁️',
        color: '#f59e0b',
        bgColor: 'rgba(245, 158, 11, 0.12)'
    },

    genai: {
        label: 'Generative AI',
        shortLabel: 'Gen AI',
        description:
            'Diffusion models, LLMs, RAG, agents, and the frontier of AI generation.',
        icon: '✨',
        color: '#a78bfa',
        bgColor: 'rgba(167, 139, 250, 0.12)'
    },

    ainews: {
        label: 'AI News',
        shortLabel: 'AI News',
        description:
            'Breaking developments, model releases, and industry analysis.',
        icon: '📡',
        color: '#34d399',
        bgColor: 'rgba(52, 211, 153, 0.12)'
    },

    statistics: {
        label: 'Statistics for AI',
        shortLabel: 'Stats',
        description:
            'Probability, statistical tests, distributions, and the math behind ML.',
        icon: '📊',
        color: '#fb923c',
        bgColor: 'rgba(251, 146, 60, 0.12)'
    }

};


/* =========================================================
   ALL CATEGORIES
   ========================================================= */

const ALL_CATEGORIES = [
    'ml',
    'dl',
    'nlp',
    'cv',
    'genai',
    'ainews',
    'statistics'
];


/* =========================================================
   SUPABASE STORAGE CONFIGURATION
   ========================================================= */

const SUPABASE_STORAGE_URL =
    typeof window !== 'undefined' &&
    window.CONFIG &&
    typeof window.CONFIG.SUPABASE_STORAGE_URL === 'string'
        ? window.CONFIG.SUPABASE_STORAGE_URL.replace(/\/+$/, '')
        : null;


/* =========================================================
   CONFIGURATION VALIDATION
   ========================================================= */

if (!SUPABASE_STORAGE_URL) {

    console.error(
        '[BlogBoard] SUPABASE_STORAGE_URL is missing from config.js'
    );

}


/* =========================================================
   CACHE
   ========================================================= */

/*
 * Stores successfully loaded category data.
 *
 * Example:
 *
 * _cache.ml = [...]
 * _cache.dl = [...]
 */

const _cache = {};


/*
 * Stores promises for requests currently in progress.
 *
 * This prevents multiple parts of the page from requesting
 * the same articles.json simultaneously.
 */

const _pendingRequests = {};


/* =========================================================
   REQUEST TIMEOUT
   ========================================================= */

/*
 * Maximum amount of time we allow one Supabase request
 * to take before abandoning it.
 *
 * This is the important fix for the infinite loading problem.
 */

const REQUEST_TIMEOUT = 10000;


/* =========================================================
   FETCH WITH TIMEOUT
   ========================================================= */

async function fetchWithTimeout(url, options = {}) {

    const controller = new AbortController();

    const timeoutId = setTimeout(() => {

        controller.abort();

    }, REQUEST_TIMEOUT);


    try {

        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });

        return response;

    } finally {

        clearTimeout(timeoutId);

    }

}


/* =========================================================
   LOAD ARTICLES FOR ONE CATEGORY
   ========================================================= */

async function loadCategoryArticles(category) {

    /*
     * Return cached data immediately.
     */

    if (_cache[category] !== undefined) {

        return _cache[category];

    }


    /*
     * If another request for this category is already running,
     * wait for that request instead of creating another one.
     */

    if (_pendingRequests[category]) {

        return _pendingRequests[category];

    }


    /*
     * Configuration check.
     */

    if (!SUPABASE_STORAGE_URL) {

        console.error(
            '[BlogBoard] Supabase Storage URL is missing.'
        );

        _cache[category] = [];

        return [];

    }


    /*
     * Build articles.json URL.
     */

    const url =
        `${SUPABASE_STORAGE_URL}/blogs/${encodeURIComponent(category)}/articles.json`;


    /*
     * Create one request promise.
     */

    const requestPromise = (async () => {

        try {

            const response =
                await fetchWithTimeout(url, {
                    method: 'GET',
                    cache: 'no-store'
                });


            /*
             * HTTP error.
             */

            if (!response.ok) {

                console.warn(
                    `[BlogBoard] ${category}/articles.json returned HTTP ${response.status}`
                );

                _cache[category] = [];

                return [];

            }


            /*
             * Parse JSON.
             */

            const data =
                await response.json();


            /*
             * Validate JSON.
             */

            if (!Array.isArray(data)) {

                console.warn(
                    `[BlogBoard] Invalid articles.json format for category: ${category}`
                );

                _cache[category] = [];

                return [];

            }


            /*
             * Save to cache.
             */

            _cache[category] = data;



            return data;

        } catch (error) {

            /*
             * AbortError means the request exceeded
             * our timeout.
             */

            if (error.name === 'AbortError') {

                console.warn(
                    `[BlogBoard] Request timed out for category: ${category}`
                );

            } else {

                console.error(
                    `[BlogBoard] Failed loading category ${category}:`,
                    error
                );

            }


            /*
             * A failed category should NEVER block
             * the rest of the website.
             */

            _cache[category] = [];

            return [];

        } finally {

            /*
             * Remove pending request.
             */

            delete _pendingRequests[category];

        }

    })();


    /*
     * Store active request.
     */

    _pendingRequests[category] = requestPromise;


    return requestPromise;
}


/* =========================================================
   GET BLOGS BY CATEGORY
   ========================================================= */

async function getBlogsByCategory(
    category,
    sort = 'newest'
) {

    const articles =
        await loadCategoryArticles(category);


    const sorted =
        [...articles].sort((a, b) => {

            const dateA =
                new Date(a.date || 0).getTime();

            const dateB =
                new Date(b.date || 0).getTime();


            if (sort === 'oldest') {

                return dateA - dateB;

            }


            return dateB - dateA;

        });


    return sorted;
}


/* =========================================================
   GET SINGLE BLOG
   ========================================================= */

async function getBlogById(id) {

    if (!id) {

        return null;

    }


    /*
     * Decode URL parameter safely.
     */

    try {

        id = decodeURIComponent(id);

    } catch (_) {

        /*
         * Keep original ID if decoding fails.
         */

    }


    /*
     * Try to determine category from ID.
     *
     * Example:
     *
     * blogs/ml/my-article.md
     */

    const parts = id.split('/');


    if (parts.length >= 3) {

        const category = parts[1];


        if (CATEGORY_META[category]) {

            const articles =
                await loadCategoryArticles(category);


            const found =
                articles.find(article =>
                    article.id === id ||
                    article.file === id
                );


            if (found) {

                return found;

            }

        }

    }


    /*
     * Fallback:
     * search every category.
     */

    for (const category of ALL_CATEGORIES) {

        const articles =
            await loadCategoryArticles(category);


        const found =
            articles.find(article =>
                article.id === id ||
                article.file === id
            );


        if (found) {

            return found;

        }

    }


    return null;
}


/* =========================================================
   GET RECENT BLOGS
   ========================================================= */

/*
 * IMPORTANT:
 *
 * We use Promise.allSettled().
 *
 * Each category request also has a timeout.
 *
 * Therefore:
 *
 * - ML fails -> other categories continue
 * - DL fails -> other categories continue
 * - one request hangs -> timeout after 10 seconds
 * - homepage never waits forever
 */

async function getRecentBlogs(limit = 6) {


    const results =
        await Promise.allSettled(

            ALL_CATEGORIES.map(
                category =>
                    loadCategoryArticles(category)
            )

        );


    const flatArticles = [];


    results.forEach((result, index) => {

        const category =
            ALL_CATEGORIES[index];


        if (
            result.status === 'fulfilled' &&
            Array.isArray(result.value)
        ) {

            flatArticles.push(
                ...result.value
            );

        } else {

            console.warn(
                `[BlogBoard] Category unavailable: ${category}`
            );

        }

    });


    /*
     * Sort newest first.
     */

    flatArticles.sort((a, b) => {

        const dateA =
            new Date(a.date || 0).getTime();

        const dateB =
            new Date(b.date || 0).getTime();


        return dateB - dateA;

    });


    /*
     * Remove duplicate article IDs.
     *
     * This protects the homepage if the same article
     * accidentally appears in multiple category files.
     */

    const uniqueArticles = [];

    const seen = new Set();


    for (const article of flatArticles) {

        const key =
            article.id ||
            article.file ||
            `${article.title}-${article.date}`;


        if (seen.has(key)) {

            continue;

        }


        seen.add(key);

        uniqueArticles.push(article);

    }


    const recent =
        uniqueArticles.slice(0, limit);



    return recent;
}


/* =========================================================
   GET TOTAL ARTICLE COUNT
   ========================================================= */

/*
 * Counts articles across all categories.
 *
 * IMPORTANT:
 *
 * We no longer make a SECOND set of network requests
 * with cache-busting timestamps.
 *
 * Instead we use loadCategoryArticles().
 *
 * That means:
 *
 * - same requests
 * - same timeout
 * - same cache
 * - no duplicate network traffic
 */

async function getTotalCount() {

    const results =
        await Promise.allSettled(

            ALL_CATEGORIES.map(
                category =>
                    loadCategoryArticles(category)
            )

        );


    let total = 0;


    results.forEach((result, index) => {

        const category =
            ALL_CATEGORIES[index];


        if (
            result.status === 'fulfilled' &&
            Array.isArray(result.value)
        ) {

            total += result.value.length;

        } else {

            console.warn(
                `[BlogBoard] Could not count category: ${category}`
            );

        }

    });


    return total;
}


/* =========================================================
   CLEAR CACHE
   ========================================================= */

function clearBlogCache() {

    Object.keys(_cache).forEach(
        key => delete _cache[key]
    );


    Object.keys(_pendingRequests).forEach(
        key => delete _pendingRequests[key]
    );
}


/* =========================================================
   DATE FORMATTING
   ========================================================= */

function formatDate(dateString) {

    if (!dateString) {

        return '';

    }


    /*
     * Handle YYYY-MM-DD safely.
     */

    const parts =
        String(dateString)
            .split('-')
            .map(Number);


    if (parts.length !== 3) {

        return dateString;

    }


    const [year, month, day] = parts;


    if (
        !year ||
        !month ||
        !day
    ) {

        return dateString;

    }


    return new Date(
        year,
        month - 1,
        day
    ).toLocaleDateString(
        'en-US',
        {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        }
    );
}